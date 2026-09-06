# Adapter Contracts

## Purpose

This document specifies the adapter contracts that carry governed memory information across the component seams defined in [`13-system-composition-boundaries.md`](13-system-composition-boundaries.md).

Components own behavior. Adapters own the seam. An adapter's job is to move a typed handoff between components without letting meaning, scope, uncertainty, or policy state fall off in transit — so implementations can integrate without redefining doctrine locally.

Every adapter here implements a component contract from `13-system-composition-boundaries.md` and inherits the ten handoff invariants defined there. This document adds what the seam itself must specify: required fields, failure modes, and rejection semantics.

## Common handoff record

All adapters exchange the cross-component handoff record defined in `13-system-composition-boundaries.md`:

```text
memory_id
source_component
target_component
handoff_reason
state_snapshot
signal_type
signal_semantics
signal_value
estimator_ref
estimator_version
calibration_ref
uncertainty_summary
evidence_refs
policy_refs
policy_version
authority_refs
permitted_action_set
certification_refs
ledger_ref
timestamp
```

Three rules make this one record shape safe across ten different seams:

1. **Each adapter declares its required subset.** Fields outside the subset are optional advisory context.
2. **Absence is absence.** A receiving component must not infer omitted authority, scope, certainty, or certification. Missing advisory fields may reduce decision quality; missing required fields fail the handoff.
3. **Rejection is the only failure mode.** A handoff that fails validation is rejected whole, with a machine-readable reason. Adapters never repair, default, or partially apply a consequential handoff.

Versioning of the record itself follows [`27-schema-registry-and-type-evolution.md`](27-schema-registry-and-type-evolution.md): an adapter that receives an unknown core schema version must not process it for consequential mutation.

## Failure modes common to all adapters

These composition failures from `13-system-composition-boundaries.md` are prohibited at every seam; each adapter section below adds its specific ones.

| Failure mode | Prohibition |
|---|---|
| Semantic type erasure | `signal_value` must travel with `signal_type` and `signal_semantics`; a bare number is not a valid consequential signal |
| Boolean coercion of uncertainty | an uncertain classification must map to an uncertain or conservative value, never to the permissive default |
| Authority leakage | recommendations, scores, and relevance never cross a seam as permissions; only `authority_refs` and `permitted_action_set` carry authority |
| Scope laundering | scope, tenancy, and sensitivity metadata survive every transformation, including summarization |
| Stale authorization | authority binds to `state_snapshot` and `policy_version`; a state change invalidates the handoff |
| Disagreement erasure | material estimator disagreement is carried in `uncertainty_summary`, not averaged away in transit |

## Adapter contracts

### Identity adapter

Implements the identity contract of `13-system-composition-boundaries.md`; doctrine in [`01-layer-model.md`](01-layer-model.md) and ADR-001.

- **Input**: artifact or artifact reference. **Output**: stable identity or address.
- **Required handoff fields**: `memory_id` (the resolved identity), `source_component`, `signal_type: identity_resolution`, `timestamp`.
- **Seam guarantees**: resolution is deterministic where doctrine requires it; the adapter never returns a "probably the same object" match as an identity. Similarity is an evidence signal and must exit through the evidence adapter instead.
- **Failure modes**: ambiguous resolution returned as identity; confidence-weighted identity substitution; identity minted for an artifact whose content could not be read.
- **Rejection**: unresolvable identity fails the handoff; downstream components receive no identity rather than a guessed one.

### Evidence adapter

Implements the evidence contract; doctrine in [`16-source-trust-and-reputation.md`](16-source-trust-and-reputation.md).

- **Input**: identity, observation, source reference. **Output**: evidence record with provenance and confidence or uncertainty signal.
- **Required handoff fields**: `memory_id`, `evidence_refs`, `signal_type`, `signal_semantics`, `estimator_ref` and `estimator_version` when the evidence is inferred, `timestamp`.
- **Seam guarantees**: source traceability survives the handoff; inferred and observed evidence remain distinguishable; source trust travels as evidence weight, never as authority.
- **Failure modes**: evidence without provenance; inferred evidence presented as observation; trust score consumed as permission.
- **Rejection**: evidence records lacking source refs are rejected; a summary is not admissible evidence for the claim it summarizes unless its own source refs are attached.

### Graph adapter

Implements the reality graph contract; doctrine in ADR-005.

- **Input**: evidence records, domain artifacts. **Output**: nodes, edges, relation confidence, provenance.
- **Required handoff fields**: `memory_id` per endpoint, `signal_type: relation`, `signal_semantics` (relation type), `signal_value` (relation confidence), `evidence_refs`, `timestamp`.
- **Seam guarantees**: deterministic and inferred relations remain distinguishable across the seam; material disagreement between relation sources stays visible.
- **Failure modes**: graph confidence consumed as mutation authority; inferred edges hardening into deterministic ones through round-trips; edge deletion crossing the seam without an authority record.
- **Rejection**: relation handoffs whose endpoints lack resolved identity are rejected back to the identity adapter.

### Lifecycle adapter

Implements the lifecycle contract; doctrine in [`02-lifecycle-state-machine.md`](02-lifecycle-state-machine.md).

- **Input**: memory unit, event, score, policy signal, transition proposal. **Output**: validated transition proposal or committed state-transition record.
- **Required handoff fields**: `memory_id`, `state_snapshot`, `signal_type: transition_proposal` or `transition_commit`, `policy_version`, `authority_refs` for commits, `ledger_ref` for commits, `timestamp`.
- **Seam guarantees**: proposal and commit are distinct message types and never coerce into each other; a commit crossing the seam carries the authority that produced it.
- **Failure modes**: proposals auto-committing on receipt; commits without reconstructable policy and state snapshots; transition records that skip states the machine does not permit.
- **Rejection**: a commit whose `state_snapshot` no longer matches current state is rejected as stale authorization and must re-enter as a proposal.

### Scoring adapter

Implements the saturation and decay contract; doctrine in [`03-scoring-and-decay.md`](03-scoring-and-decay.md) and [`09-calibration-protocol.md`](09-calibration-protocol.md).

- **Input**: memory unit, interaction history, pressure. **Output**: sigma, decay profile, candidate routing signal, uncertainty metadata.
- **Required handoff fields**: `memory_id`, `signal_type: saturation`, `signal_semantics` (declared score meaning: probabilistic or ordinal/routing), `signal_value`, `estimator_ref`, `estimator_version`, `calibration_ref`, `uncertainty_summary`, `timestamp`.
- **Seam guarantees**: score semantics are declared, not assumed; calibration scope and version travel with every consequential score; out-of-scope scores are flagged, not silently reused.
- **Failure modes**: sigma consumed as truth or permission; a routing score acquiring probabilistic meaning downstream; calibration scope dropped so stale claims persist across distribution shift.
- **Rejection**: consequential scores without `calibration_ref` are rejected for promotion routing and may be used only for ephemeral decisions policy explicitly permits.

### PAMA adapter

Implements the governance contract and the action-selection contract; doctrine in [`04-governance-and-pama.md`](04-governance-and-pama.md) and [`33-pama-decision-table.md`](33-pama-decision-table.md).

- **Input**: requested mutation, memory state, risk, evidence, actor, reversibility, estimator outputs, uncertainty. **Output**: PAMA outcome and permitted action set.
- **Required handoff fields**: `memory_id`, `state_snapshot`, `signal_type: authority_decision`, `authority_refs`, `permitted_action_set`, `policy_refs`, `policy_version`, `uncertainty_summary` of consumed estimates, `ledger_ref`, `timestamp`.
- **Seam guarantees**: the outcome is deterministic or formally bounded for the committed inputs and policy snapshot; prohibited actions are absent from `permitted_action_set` rather than flagged inside it; downstream selection — deterministic or stochastic — occurs only inside the permitted set.
- **Failure modes**: authority inferred from confidence at the seam; permitted sets widened in transit; a blocked action reappearing downstream; an authority decision reused after `state_snapshot` or `policy_version` changed.
- **Rejection**: mutation requests whose actor authority cannot be reconstructed are rejected with `block`; the adapter never forwards them for "best-effort" handling.

### Certification adapter

Implements the certification contract; doctrine in ADR-003.

- **Input**: candidate memory, evidence, authority outcome, verification material. **Output**: certification status, scope, certificate reference.
- **Required handoff fields**: `memory_id`, `certification_refs`, `signal_type: certification_status`, scope of validity inside `signal_semantics`, `evidence_refs` the certificate binds, `policy_version`, `timestamp`.
- **Seam guarantees**: certification is scoped — the certificate names what was verified and under which policy and evidence context; the certifier is independent of the proposing estimator; revocation crosses the seam with the same fidelity as issuance.
- **Failure modes**: confidence becoming certification; certificates outliving the evidence or policy context they bound; scope of a narrow certification silently widening downstream.
- **Rejection**: crystallization handoffs without a valid, in-scope `certification_refs` entry are rejected regardless of any other field, per the crystallization rule in `04-governance-and-pama.md`.

### Runtime memory adapter

Implements the runtime memory contract and recall admission; doctrine in [`26-governed-recall-planner.md`](26-governed-recall-planner.md) and [`29-actor-scope-consent-and-tenancy.md`](29-actor-scope-consent-and-tenancy.md).

- **Input**: memory units, graph relations, context request, policy constraints. **Output**: retrieval candidates, admitted memory, assembled context.
- **Required handoff fields**: `memory_id` per admitted unit, `signal_type: recall_admission`, admission outcome inside `signal_semantics`, scope and sensitivity survival per unit, `policy_version`, `timestamp`.
- **Seam guarantees**: candidate generation may be probabilistic; admission is governed — scope, tenancy, sensitivity, dispute, and policy constraints apply between retrieval and admission, on the adapter's receiving side of the seam; assembled context references its admission decisions.
- **Failure modes**: relevance consumed as access permission; scope metadata stripped during assembly or summarization; disputed memory entering canonical use; hidden durable mutation on the read path.
- **Rejection**: candidates that arrive without scope metadata are rejected from admission — unknown scope is treated as out-of-scope, never as local.

### Correction and dispute adapter

Implements the correction and dispute contract; doctrine in [`17-conflict-resolution-engine.md`](17-conflict-resolution-engine.md).

- **Input**: contradiction, user correction, failed verification, expired source. **Output**: dispute, correction, demotion, reconciliation, or pruning proposal.
- **Required handoff fields**: `memory_id`, `signal_type: dispute` or `correction_proposal`, `evidence_refs` for the triggering conflict, `state_snapshot`, `timestamp`; `authority_refs` when the output is a committed correction.
- **Seam guarantees**: conflict interpretation may remain probabilistic, but the consequence crossing the seam is governed; prior state is preserved and supersession-linked per [`18-temporal-causality-layer.md`](18-temporal-causality-layer.md); an open dispute travels with the memory it disputes.
- **Failure modes**: corrections overwriting history instead of superseding it; dispute state dropped in transit so downstream consumers see a clean memory; auto-resolution by newest-wins or highest-confidence-wins.
- **Rejection**: correction commits without provenance and ledger requirements are rejected back to proposal state.

### Governance context projection adapter

Implements the vendor-neutral governance-facing projection defined in [`profiles/governance-context-projection-profile.md`](profiles/governance-context-projection-profile.md) and proposed ADR-029.

This adapter differs from the internal component adapters above: it produces a **derived consumer-facing projection** rather than a canonical mutation handoff.

- **Input**: governed-recall results plus canonical identity, evidence, scope, lifecycle/validity, rationale, authority-context, and outcome references that are permitted for the requesting purpose.
- **Output**: an object conforming to [`../schemas/governance-context-projection.schema.json`](../schemas/governance-context-projection.schema.json).
- **Required projection fields**: `projection_id`, `purpose`, `current_context_ref`, `source_memory_refs`, `scope`, `precedents`, `derivation`, `generated_at`.
- **Seam guarantees**: projection remains reconstructable; source memory and provenance remain resolvable; positive and negative precedent remain distinguishable; material conditions preserve match/mismatch/unknown rather than collapsing into a broad action label; validity and scope survive projection; consumer-specific verdict and risk semantics are absent.
- **Failure modes**: prior approval crossing the seam as standing permission; policy-generated allow presented as independent human precedent; negative precedent erased by frequency; semantic similarity becoming authority; sensitive raw rationale copied when a bounded reference would suffice; a derived projection becoming the only source of an underlying memory fact.
- **Rejection**: projections with unknown/invalid source identity, missing scope, unreconstructable derivation, or schema-invalid consumer authority fields are rejected whole. The adapter does not repair them into a permissive default.

The ownership boundary is deliberate:

```text
Agent Memory core
  -> governance context projection
  -> consumer adapter
```

The governance-context adapter may expose vendor-neutral context. A DashClaw adapter, AGT/ACS adapter, or other consumer adapter owns translation into that consumer's risk, verdict, approval, and API vocabulary.

### Conformance adapter

Implements the conformance contract; doctrine in [`06-conformance-test-plan.md`](06-conformance-test-plan.md).

- **Input**: fixtures, implementation behavior, report data. **Output**: conformance result, calibration metrics, failure report.
- **Required handoff fields**: `signal_type: conformance_result`, report reference conforming to [`../schemas/conformance-report.schema.json`](../schemas/conformance-report.schema.json), fixture identifiers, `estimator_version` and `calibration_ref` for calibration claims, `timestamp`.
- **Seam guarantees**: stochastic systems are judged against invariants, not identical sampled outputs; trap-class failures are reported as failures, never as exemptions; results identify the doctrine version they tested against.
- **Failure modes**: cherry-picked trials crossing the seam as representative results; exemptions accumulating without expiry; calibration claims outliving their scope.
- **Rejection**: reports that fail schema validation are rejected whole; a partially valid conformance claim is not a weaker claim, it is no claim.

## Worked handoff examples

### Identity handoff

The evidence component asks the identity component to resolve a build artifact:

```json
{
  "memory_id": "uor:blake3:9f41c2...",
  "source_component": "identity",
  "target_component": "evidence",
  "handoff_reason": "artifact_resolution",
  "signal_type": "identity_resolution",
  "signal_semantics": "deterministic_content_address",
  "timestamp": "2026-08-10T21:04:00Z"
}
```

Had resolution been ambiguous, the correct handoff is a rejection with reason `unresolvable_identity` — not the closest match. Similarity between artifacts, if useful, exits later as an evidence record with its own estimator provenance.

### Scoring handoff

The saturation component routes a candidate signal to the lifecycle component:

```json
{
  "memory_id": "uor:blake3:9f41c2...",
  "source_component": "scoring",
  "target_component": "lifecycle",
  "handoff_reason": "candidate_routing",
  "signal_type": "saturation",
  "signal_semantics": "ordinal_routing_score",
  "signal_value": 0.86,
  "estimator_ref": "mts-saturation",
  "estimator_version": "v2",
  "calibration_ref": "cal-2026-08",
  "uncertainty_summary": { "band": [0.79, 0.91], "estimator_disagreement": false },
  "timestamp": "2026-08-10T21:05:00Z"
}
```

`signal_semantics` declares this an ordinal routing score: the lifecycle component may propose candidacy but must not read 0.86 as an 86% probability of anything. Without `calibration_ref`, this handoff is invalid for promotion routing.

### PAMA handoff

The governance component returns an authority envelope for the proposed promotion:

```json
{
  "memory_id": "uor:blake3:9f41c2...",
  "source_component": "governance",
  "target_component": "lifecycle",
  "handoff_reason": "promotion_authority",
  "state_snapshot": "reinforced@v14",
  "signal_type": "authority_decision",
  "signal_semantics": "pama_outcome:require_review",
  "authority_refs": ["pama:decision:5521"],
  "permitted_action_set": ["enter_pending_verification", "collect_more_evidence", "defer"],
  "policy_refs": ["policy:promotion"],
  "policy_version": "p-14",
  "uncertainty_summary": { "consumed_estimates": ["saturation"], "authority_uncertainty": "none" },
  "ledger_ref": "ledger:evt:88412",
  "timestamp": "2026-08-10T21:05:02Z"
}
```

`crystallize` is absent from the permitted set, so no downstream planner — deterministic or stochastic — can select it. If the memory's state changes before the lifecycle component commits, `state_snapshot` no longer matches and the envelope is stale: back to PAMA, not forward to commit.

### Certification handoff

After review resolves, the certification component confirms the durable transition:

```json
{
  "memory_id": "uor:blake3:9f41c2...",
  "source_component": "certification",
  "target_component": "lifecycle",
  "handoff_reason": "crystallization_gate",
  "signal_type": "certification_status",
  "signal_semantics": "scope:project_decisions;consequence:crystallization",
  "certification_refs": ["cert:2026:0142"],
  "evidence_refs": ["ev:commit:aa10", "ev:review:77"],
  "policy_version": "p-14",
  "timestamp": "2026-08-10T21:40:00Z"
}
```

The certificate binds scope, evidence, and policy version. A later request to reuse `cert:2026:0142` for a different memory, a broader scope, or a drifted policy version fails M-CERT in [`33-pama-decision-table.md`](33-pama-decision-table.md).

## Conformance

The composition paths in `13-system-composition-boundaries.md` are the adapter test plan: each path crosses at least two of these seams, and tests should inject uncertainty, disagreement, and staleness at the seam rather than only inside components. Existing fixtures exercising seam behavior include [`../fixtures/authority-laundering.json`](../fixtures/authority-laundering.json) (authority leakage), [`../fixtures/cross-tenant-relevance-trap.json`](../fixtures/cross-tenant-relevance-trap.json) (relevance versus admission), [`../fixtures/stochastic-retrieval-policy-envelope.json`](../fixtures/stochastic-retrieval-policy-envelope.json) (selection inside the permitted set), and [`../fixtures/policy-estimator-version-drift.json`](../fixtures/policy-estimator-version-drift.json) (stale authorization).

Governance-projection V0.1 adds [`../fixtures/governance-precedent-material-match.json`](../fixtures/governance-precedent-material-match.json) and [`../fixtures/governance-precedent-material-mismatch.json`](../fixtures/governance-precedent-material-mismatch.json). These prove that useful precedent context can cross a consumer seam while final authority remains downstream.

## Doctrine

Adapters do not make decisions. They make decisions portable.

Governance Context Projection sharpens that rule: some adapters do not even carry a decision. They carry remembered context from which a separate governance system may make one.

Whatever a component may not do inside its own boundary, it may not achieve by handing data across a seam that strips the constraint. The handoff record exists so that authority, scope, uncertainty, and provenance arrive with the payload — or the payload does not arrive.
