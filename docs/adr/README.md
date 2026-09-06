# Architecture Decision Records

This directory records architectural decisions for the Agent Memory doctrine.

## Status semantics

ADR status describes **doctrine maturity**, not implementation maturity.

| Status | Meaning |
|---|---|
| Proposed | A decision candidate under active evaluation. Required evidence, follow-up, or doctrine integration is incomplete. |
| Accepted | The decision is canonical Agent Memory doctrine. Implementations may still be conceptual, partial, experimental, or absent. |
| Superseded | A later ADR replaces this decision. Historical rationale remains useful. |
| Rejected | The proposal was evaluated and intentionally not adopted. |

An `Accepted` ADR does **not** claim:

- every related repository implements it;
- runtime enforcement is complete everywhere;
- every behavioral conformance case passes in production;
- the decision can never be revised.

Implementation maturity is tracked separately through schemas, fixtures, implementation maps, runtime evidence, quality metrics, and conformance reports.

## Current doctrine state

```text
ADR-001 through ADR-020: Accepted
ADR-021: Proposed
ADR-022: Accepted
ADR-023: Proposed
ADR-024: Accepted
ADR-025: Proposed
ADR-026: Proposed
ADR-027: Proposed
ADR-028: Accepted
ADR-029: Proposed
ADR-030: Accepted
ADR-031: Accepted
ADR-032: Accepted
ADR-033: Accepted
ADR-034: Accepted
ADR-035: Accepted
ADR-036: Accepted
ADR-037: Accepted
```

ADRs 001-020, ADR-022, ADR-024, ADR-028, ADR-030, ADR-031, ADR-032, ADR-033, ADR-034, ADR-035, ADR-036, and ADR-037 have satisfied their doctrine-maturity gates.

Several accepted decisions deliberately required stronger-than-documentation evidence. ADR-020 required executable end-to-end governed-consequence evidence and adversarial negative paths. ADR-024 required executable shared-write coordination evidence. ADR-034 required a real procedural-memory vertical slice proving that retained/recalled skills do not become standing execution or metamemory authority. ADR-035 required an executable Cognitive Mesh path plus native first-party Cognitive Metabolism evidence crossing the mesh/PAMA/recall boundary without provider authority laundering.

## Current status policy

A decision may move from Proposed to Accepted when:

1. its architectural boundary is sufficiently defined;
2. it is integrated consistently into canonical doctrine;
3. known material contradictions have been resolved or documented;
4. required foundational documentation exists;
5. any schema/fixture prerequisites named by the ADR are satisfied;
6. any stronger runtime/evidence gate named by the ADR is satisfied.

Satisfying an implementation prerequisite does not silently promote a Proposed ADR when the ADR or governing issue reserves maturity review as a separate decision.

The evidence policy is source-neutral. Native authorship, maintainer status, external publication, implementation popularity, AI generation, or prior acceptance do not make a claim immune to challenge. See [`../policies/EVIDENCE_PROMOTION.md`](../policies/EVIDENCE_PROMOTION.md).

## Decision families

### Governed uncertainty

[`ADR-020`](ADR-020-probabilistic-discovery-deterministic-governance.md) is **Accepted**.

Its central boundary is:

```text
estimate / learned proposal
  -> governance envelope
  -> permitted action set
  -> selected action
  -> committed consequence
```

The repository has executable evidence for stochastic containment, cross-scope recall, concurrency conflict handling, deletion residue, transitive deletion behavior, reconstructable receipts, adversarial boundary enforcement, and a pinned real-substrate path. Acceptance does not upgrade the narrow reference adapter to universal production conformance.

ADR-032 strengthens this boundary for canonical structural mutation. ADR-034 applies the same separation to reusable procedures and memory-management skills: learned discovery may propose, but retained procedure does not become action or memory-profile authority.

### Portable memory-governance evidence

[`ADR-021`](ADR-021-portable-memory-governance-evidence-boundary.md) remains **Proposed**.

```text
Agent Memory
  owns memory semantics, PAMA, lifecycle, canonical receipts
        |
        v
portable evidence projection
        |
        v
external trust / attestation system
  verifies binding, integrity, execution correlation
```

The external verifier does not acquire authority to redefine memory-specific permission or infer lifecycle satisfaction from cryptographic integrity alone. Acceptance requires the interoperability and deletion-completeness evidence named by ADR-021.

### Memory isolation domains

[`ADR-022`](ADR-022-memory-isolation-domains-and-controlled-boundary-crossing.md) is **Accepted**.

```text
same agent / same store
        !=
same authorized memory domain
```

Project, task, workspace, session, purpose, tenant, and shared-memory boundaries are logical authority domains rather than mere storage filters. Sharing, exporting, copying, deriving, or broadening scope is a governed consequence. Derived state must not silently gain broader scope than its sources.

ADR-034 uses this boundary directly: a highly relevant procedural skill from another project or tenant remains inadmissible without governed crossing.

### Corrections and durable state

[`ADR-023`](ADR-023-corrections-are-supersession-not-deletion.md) remains **Proposed**. It generalizes durable correction as append-only supersession rather than destructive erasure.

[`ADR-025`](ADR-025-durable-decision-overwrites-require-explicit-authority.md) remains **Proposed**. The #144 reference slice exercises exact overwrite-authority validation, PAMA, append-only supersession, stale proposals, agent-collusion refusal, authority-binding failures, and PAMA non-override, but its doctrine maturity remains a separate decision.

[`ADR-027`](ADR-027-rejected-values-require-governed-readmission.md) remains **Proposed**. It requires a corrected/rejected value to pass governed re-admission rather than silently returning under a fresh identity.

### Shared durable-memory writes

[`ADR-024`](ADR-024-shared-memory-writes-require-prewrite-claims.md) is **Accepted**.

```text
shared write intent
  -> bounded pre-write claim / lease / equivalent coordination
  -> current-state and conflict validation
  -> PAMA authority evaluation
  -> durable mutation or refusal
```

A claim grants only the bounded opportunity to attempt a shared mutation. It cannot loosen PAMA.

### Source-neutral evidence

[`ADR-026`](ADR-026-origin-is-provenance-not-evidentiary-authority.md) remains **Proposed**.

Its candidate rule is that origin establishes provenance, not evidentiary authority. Human, agent, maintainer, imported, or generated claims remain subject to the same evidence/currentness scrutiny appropriate to their consequence.

### Implementation portability

[`ADR-028`](ADR-028-language-neutral-core-and-optional-implementation-profiles.md) is **Accepted**.

```text
normative doctrine / schemas / fixtures
        !=
reference implementation language
        !=
optional implementation or interoperability profile
```

Python may remain practical reference/integration tooling. Rust remains first-class for high-assurance or performance-sensitive components. UOR, AGT, MCP, and other ecosystems may supply optional profiles without becoming the definition of Agent Memory.

### Governance Context Projection

[`ADR-029`](ADR-029-governance-projection-is-derived-context-not-authority.md) remains **Proposed**.

```text
canonical Agent Memory primitives
        |
        v
Governance Context Projection
  evidence / precedent / material conditions
        |
        v
consumer-specific adapter
  policy vocabulary / approval / enforcement
```

The projection is reconstructable derived context, not canonical truth, standing permission, or a final consumer verdict. Acceptance requires the reference builder, near-match/adversarial evidence, scope/provenance preservation, privacy/minimization evidence, and a consumer integration named by ADR-029.

### Versioned temporal-policy projections

[`ADR-030`](ADR-030-temporal-policy-consumers-require-versioned-compatible-projections.md) is **Accepted**.

```text
canonical Agent Memory state
        |
        v
versioned consumer projection
        |
        v
compatibility / currentness evaluation
        |
        v
external temporal or authorization consumer
```

Serialization success is not semantic compatibility. Historical temporal evidence is not current authority. Compatibility binds source schema/currentness, projection identity/version, consumer capabilities, isolation strategy, and evidence.

### Cryptographic temporal commitments

[`ADR-031`](ADR-031-temporal-claims-require-deterministic-content-commitments.md) is **Accepted**.

```text
temporal claims + payload/schema/scope/order
        |
        v
deterministic content commitment
        |
        +--> signer attestation
        +--> optional external witness evidence
        |
        v
separate Agent Memory currentness + PAMA evaluation
```

Historical identity, signer trust, witnessed time, lifecycle currentness, and authority remain distinct claims.

### Governed mutable memory structure

[`ADR-032`](ADR-032-governed-mutable-memory-structure.md) is **Accepted**.

```text
learned / probabilistic structural discovery
        |
        v
structural proposal
        |
        v
deterministic semantic / migration / dependency / scope analysis
        |
        v
deterministic authorized envelope OR explicit human authority
        |
        v
committed structural consequence
```

Memory shape may adapt, but authority over canonical structural mutation may not be probabilistic. Derived/rebuild-only changes may be autonomous under deterministic maintenance policy. Bounded additive changes require a deterministic authorized envelope. Semantic migrations and destructive/cross-scope/authority-bearing changes require explicit authority unless future doctrine narrows an exact delegated class.

PAMA 1.2 remains conservatively stricter for `domain_schema_mutation` until narrower autonomous evidence is earned.

### Capability-oriented composition

[`ADR-033`](ADR-033-capabilities-are-independently-declared-and-deterministically-composed.md) is **Accepted**.

```text
component identity != capability identity

required capability + maturity/posture
  -> deterministic compatibility resolution
  -> selected/composed implementation
  -> normal Agent Memory authority/admission remains controlling
```

A component may expose many independently matured capabilities, and several components may expose the same capability. Ambiguous overlap must resolve through an explicit deterministic rule/composition or fail explicitly. Fallback cannot silently downgrade maturity, scope/isolation, currentness, deletion, failure, or authority posture.

The #287/#290 reference slice supplies machine-readable declarations and deterministic routing evidence. EvolveAI and CodeGenome remain evidence-bounded example declarations rather than automatically qualified providers.

### Procedural / skill memory

[`ADR-034`](ADR-034-procedural-memory-is-not-execution-authority.md) is **Accepted**.

Its central boundary is:

```text
skill retention
  != retrieval
  != recall admission / activation
  != action authority
  != execution evidence
```

A remembered procedure may shape a plan after governed admission. Actual actions remain under Runtime/Agent-Governance authority. Correction uses current-state validation, exact-content approval binding when review is required, and supersession. High-relevance foreign-scope candidates remain inadmissible. Revocation removes current influence without falsely claiming physical erasure. Metamemory cannot apply itself through ordinary skill activation and instead becomes a separate PAMA/ADR-032 profile/policy proposal.

Acceptance is backed by the #295 reference vertical slice and the focused exact-head evidence workflow:

- [`../programs/runtime-evidence/procedural-memory.md`](../programs/runtime-evidence/procedural-memory.md)
- `reference/agentmem_ref/contracts/capabilities.py`
- `reference/agentmem_ref/memory/procedural_memory.py`
- `reference/tests/test_component_capabilities.py`
- `reference/tests/test_procedural_memory.py`
- `reference/run_procedural_memory.py`
- `.github/workflows/procedural-memory-evidence.yml`

The adversarial path explicitly proves that approval for one procedure payload cannot commit a substituted payload. Acceptance remains bounded to the reference evidence and does not claim process-restart durability or universal production conformance.

### Governed cognitive framework

[`ADR-035`](ADR-035-agent-memory-is-a-governed-cognitive-framework.md) is **Accepted**.

Its canonical system identity is:

```text
Agent Memory
  -> shared Cognitive Mesh
  -> bounded Cognitive, Reality, and Authority planes
  -> independently composed/qualified implementations
  -> PAMA-governed consequence
```

ADR-035 makes the cognitive substrate explicit without reversing ADR-033. Module identity, component identity, and capability identity remain distinct.

The first-party responsibility mapping treats EvolveAI as the initial Cognitive Metabolism implementation and CodeGenome as the initial Code Reality Graph implementation. Those mappings do not promote capability maturity, make either provider's internal ontology canonical, or require immediate repository/submodule consolidation.

Acceptance is backed by:

- the Cognitive Mesh contract and three-plane integration in canonical architecture documentation;
- PR #338's executable reference path and adversarial authority-containment/module-replacement evidence;
- PR #339's canonical documentation alignment and requirement-by-requirement acceptance matrix;
- PR #340, merged at `5ef4f6936cbe0af4846135bee0562c4d4c23a3ab`, which executes pinned `EvolveAI@21161ce7b88dbffeb7ed59757b4d02d24a9c2acd` native lifecycle synthesis, retains the raw provider artifact, normalizes it through the versioned Cognitive Metabolism adapter, and carries it through Cognitive Mesh, PAMA, durable commit/refusal, governed recall, and active cognition;
- [`../programs/runtime-evidence/adr-035-acceptance-matrix.md`](../programs/runtime-evidence/adr-035-acceptance-matrix.md), which records all nine acceptance requirements as satisfied at their bounded evidence boundary.

Acceptance does not claim a complete brain implementation, universal provider conformance, mature prediction/world modeling, or automatic maturity promotion for EvolveAI or CodeGenome.

## Remaining Proposed ADRs

The remaining Proposed decisions intentionally stay separate:

- [`ADR-021`](ADR-021-portable-memory-governance-evidence-boundary.md): portable memory-governance evidence with external trust/attestation systems;
- [`ADR-023`](ADR-023-corrections-are-supersession-not-deletion.md): generalized correction-as-supersession doctrine;
- [`ADR-025`](ADR-025-durable-decision-overwrites-require-explicit-authority.md): explicit authority for durable decision overwrite;
- [`ADR-026`](ADR-026-origin-is-provenance-not-evidentiary-authority.md): source-neutral evidence authority;
- [`ADR-027`](ADR-027-rejected-values-require-governed-readmission.md): governed re-admission of rejected values;
- [`ADR-029`](ADR-029-governance-projection-is-derived-context-not-authority.md): vendor-neutral governance context projection.

These must not be collapsed into a generic "memory safety" claim. Each has its own evidence and acceptance boundary.

## Canonical references

- [`../01-layer-model.md`](../01-layer-model.md)
- [`../04-governance-and-pama.md`](../04-governance-and-pama.md)
- [`../06-conformance-test-plan.md`](../06-conformance-test-plan.md)
- [`../11-component-architecture.md`](../11-component-architecture.md)
- [`../17-conflict-resolution-engine.md`](../17-conflict-resolution-engine.md)
- [`../24-determinism-probability-and-governed-uncertainty.md`](../24-determinism-probability-and-governed-uncertainty.md)
- [`../25-governed-uncertainty-documentation-conformance-audit.md`](../25-governed-uncertainty-documentation-conformance-audit.md)
- [`../26-governed-recall-planner.md`](../26-governed-recall-planner.md)
- [`../27-schema-registry-and-type-evolution.md`](../27-schema-registry-and-type-evolution.md)
- [`../28-retention-deletion-and-tombstones.md`](../28-retention-deletion-and-tombstones.md)
- [`../29-actor-scope-consent-and-tenancy.md`](../29-actor-scope-consent-and-tenancy.md)
- [`../30-memory-observability-and-audit-events.md`](../30-memory-observability-and-audit-events.md)
- [`../31-recovery-rollback-and-replay.md`](../31-recovery-rollback-and-replay.md)
- [`../32-memory-quality-metrics.md`](../32-memory-quality-metrics.md)
- [`../34-adapter-contracts.md`](../34-adapter-contracts.md)
- [`../41-memory-isolation-domains-and-governed-crossing.md`](../41-memory-isolation-domains-and-governed-crossing.md)
- [`../42-governed-mutable-memory-fabric.md`](../42-governed-mutable-memory-fabric.md)
- [`../programs/memory-modules/README.md`](../programs/memory-modules/README.md)
- [`../programs/memory-modules/capability-vocabulary.md`](../programs/memory-modules/capability-vocabulary.md)
- [`../programs/memory-modules/external-capability-frontier.md`](../programs/memory-modules/external-capability-frontier.md)
- [`../programs/runtime-evidence/procedural-memory.md`](../programs/runtime-evidence/procedural-memory.md)
- [`../profiles/durable-decision-memory-profile.md`](../profiles/durable-decision-memory-profile.md)
- [`../profiles/governance-context-projection-profile.md`](../profiles/governance-context-projection-profile.md)
- [`../profiles/temporal-commitment-evidence-profile.md`](../profiles/temporal-commitment-evidence-profile.md)

### Same-owner components are first-party modules

[`ADR-036`](ADR-036-same-owner-components-are-first-party-modules.md) is **Accepted**.

A component sharing Agent Memory's owner is a first-party module candidate, not
an attributed provider. Adoption is wholesale and unrestricted; the adopted work
is named for the Agent Memory contract it implements rather than for its
originating repository. CodeGenome-derived work is Agent Memory's **Code Reality
Graph (CRG)** module; EvolveAI-derived work is Agent Memory's **Cognitive
Metabolism** module.

The test is ownership, not licence: a licence constrains licensees, and the owner
is not one. Lineage stays recorded in
[`../40-aligned-projects-and-intellectual-lineage.md`](../40-aligned-projects-and-intellectual-lineage.md)
and [`../08-source-material-index.md`](../08-source-material-index.md) because
intellectual history has value, but provenance is not an attribution obligation.

Nothing changes for genuinely third-party components. UOR Framework, Graphiti,
Hindsight, and MemOS keep their reuse postures and continue to qualify through
the component-qualification path with `authority_effect: none`.

### Fail-closed review requires a remediation path

[`ADR-037`](ADR-037-fail-closed-review-requires-a-remediation-path.md) is **Accepted**.

`require_review` is to fail closed, and must not do so until the remediation path
is traversable. `enter_pending_verification`, `collect_more_evidence`, and
`defer` are named in every blocking envelope and consumed by nothing; parking
becomes a real state generalizing `DurableDecisionRegistry`'s PENDING lifecycle.

Sufficiency is a **separation-of-parties** test, not a human test. The codebase
already admits `delegated_policy` as non-human authority at low and medium risk
and requires human confirmation only at high/critical. Agent-produced evidence
may exceed human ratification in value; provenance class is not a proxy for
evidential quality.

The bar is **independence**, and repetition is not independence:
`authority_laundering_harness` holds `repetition_not_independent_corroboration`
and `autonomous_maintenance_harness` refuses row count as corroboration.
Evidence from N agents sharing a substrate, model, or upstream observation is
one evidence.

Four owner rulings are recorded. **Self-produced evidence is permissible;
self-certified sufficiency is not** — a blocked agent may run a test or generate
a receipt, but may not declare its own output sufficient, and resumption is an
evaluator operation. Independence is defined by **evidential lineage and shared
failure domains**, not agent identity, and a second deterministic reproduction
validates one evidence item rather than adding a second. Evidential classes are
**ranked**: artifact-bound and reproducible satisfy directly, a calibrated
estimator may only contribute and never discharges alone. `delegated_policy` at
medium risk needs **one** separated principal, not two -- the
`minimum_independent_human_evidence >= 2` rule governs creation of reusable
authority from precedent and must not be generalized into a quorum.

Four variables are kept deliberately distinct -- authority separation, evidence
qualification, independence, and risk -- because collapsing them is how
governance becomes numerology.

Acceptance is doctrine, not implementation. The implementation order is rigid:
parked state, then evidence qualification and dependence lineage, then governed
resumption, and only then the fail-closed conversion of the 51 callers.
