# Schema Registry and Type Evolution

> Canonical requirements: [ADR-014](adr/ADR-014-schema-registry-and-type-evolution-are-needed.md) and [ADR-032](adr/ADR-032-governed-mutable-memory-structure.md)

## Purpose

Agent Memory needs stable semantic contracts without freezing implementation experimentation or domain evolution.

The schema registry defines which fields and meanings belong to doctrine-level interoperability, how those types evolve, and how implementations extend them without silently changing semantics.

ADR-032 adds a second requirement: **memory structure may evolve, but canonical structural mutation authority may not be probabilistic.** Schema/type evolution therefore needs both compatibility mechanics and an explicit authority/lifecycle boundary.

## Core rule

```text
schema compatibility != field-name compatibility only
```

If two systems both emit `confidence: 0.8` but one means semantic similarity and the other means calibrated factual probability, the schemas are semantically incompatible even if JSON validation passes with enthusiasm.

A second rule now applies:

```text
structural discovery != structural commit authority
```

A learned or probabilistic component may discover a useful candidate field, entity, relation, or model. It may not commit canonical meaning merely because the proposal scores well.

## Registry layers

### Doctrine core

Stable cross-implementation concepts such as:

- memory identity
- lifecycle state
- acquisition mode
- provenance
- scope/tenant
- sensitivity labels
- authority references
- policy version
- certification state
- dispute/supersession state
- estimator provenance
- uncertainty representation
- deletion/tombstone state
- decision receipt

Doctrine-core changes use normal ADR/schema governance and are not ordinary runtime domain-schema adaptation.

### Application/domain ontology

Deployment- or application-specific entities, relations, fields, constraints, and interpretation rules.

Examples:

```text
Project -> HAS_RELEASE_CHANNEL -> ReleaseChannel
Customer -> HAS_CONTRACT -> Contract
```

Domain structure may legitimately evolve at runtime, but consequential changes are governed under ADR-032 and PAMA.

### Derived/physical representation

Indexes, embeddings, graph materializations, caches, learned representations, and storage-specific layouts.

These may change without becoming canonical semantic mutations when meaning, authority, provenance, scope, lifecycle, and currentness remain unchanged.

### Extension layer

Implementation-specific fields may be added under explicit namespacing or extension objects.

Example:

```json
{
  "extensions": {
    "codegenome": {...},
    "evolveai": {...}
  }
}
```

Extensions must not redefine core-field meaning.

## Required versioning

Each doctrine-level serialized object should identify a schema version.

Recommended:

```text
schema_name
schema_version
```

Version semantics should distinguish:

- backward-compatible additive change
- compatible semantic clarification
- breaking field/type change
- breaking semantic change

A semantic change can be breaking even when the JSON type does not change.

For runtime domain schemas, implementations should additionally preserve a stable schema/model identity, current/superseded state, migration lineage, and compatibility/dependency evidence sufficient to reconstruct which interpretation governed a durable memory.

## Type evolution rules

### Additive field

May be backward compatible when optional and existing semantics remain valid.

For runtime domain shape, an additive field is not automatically autonomous. ADR-032 S1 eligibility also depends on bounded scope, preserved historical interpretation, no authority/isolation widening, no destructive migration, deterministic impact classification, and rollback/reversibility posture.

### New enum member

Potentially breaking for closed consumers. Consumers should define unknown-value behavior.

### Changed field meaning

Breaking. Requires a new schema version or explicit migration.

For durable domain state this is an ADR-032 S2-style semantic change by default, not a harmless rename hidden behind syntactic compatibility.

### Optional to required

Breaking unless all stored objects are migrated.

### Scalar to structured uncertainty

Breaking unless the old scalar remains interpretable through an explicit compatibility adapter.

### Retiring a field/type/relation

Retirement is not complete merely because new writes stop using the old shape.

Before retirement, the system should account for:

- live canonical objects;
- historical interpretation requirements;
- derived projections and indexes;
- module/consumer dependencies;
- migration results;
- deletion/residue obligations;
- rollback requirements.

Prefer supersession before retirement when historical interpretation or rollback matters.

## Structural mutation classes

ADR-032 defines the authority posture for runtime structural evolution:

| Class | Typical change | Default posture |
|---|---|---|
| S0 | derived/index/rebuild-only change with preserved semantics | autonomous under deterministic maintenance policy |
| S1 | bounded additive local extension with rollback and no authority widening | autonomous only when deterministic policy proves the exact bounded envelope |
| S2 | semantic reinterpretation or migration-bearing change | user-visible proposal and authorized human decision by default |
| S3 | destructive, cross-scope, isolation-, policy-, or authority-bearing change | explicit authorized human decision; stricter policy may block |

Probabilistic discovery may propose any class. It cannot classify itself into a lower-authority class for commit purposes.

A structural-impact record should preserve where applicable:

```text
current_schema_ref
proposed_schema_ref
structural_class
semantic_diff
tenant / isolation domains
scope / isolation impact
affected-state / blast-radius evidence
dependent modules / projections / consumers
migration requirement
information-loss posture
reversibility / rollback ref
rebuild / residue obligations
source / estimator evidence
state + dependency snapshot digests
deterministic classifier + policy version
authority / approval refs
```

## Semantic types that must not collapse

Keep separate:

```text
confidence
probability
similarity
trust
saturation
relevance
sensitivity
authority
certification
```

Likewise:

```text
proposal
permitted_action_set
selected_action
committed_transition
```

And for structural evolution:

```text
structural proposal
structural impact classification
structural authorization
migration execution
schema activation
schema rollback
schema retirement
```

## Estimator provenance type

A consequential estimate should be representable as:

```json
{
  "signal_type": "semantic_relevance",
  "value": 0.91,
  "value_semantics": "cosine-derived ranking score, not calibrated probability",
  "estimator_id": "retriever-x",
  "estimator_version": "3.2",
  "calibration_ref": null,
  "uncertainty": null,
  "scope": "project-A"
}
```

The same discipline applies when an estimator proposes a schema/domain-model change. Its confidence is evidence about the proposal, never structural authority. Repetition, prior autonomous success, or disagreement among probabilistic estimators likewise cannot lower the deterministic structural authority floor.

## Uncertainty type

Support multiple representations rather than forcing one universal confidence scalar.

Possible forms:

- categorical: low / medium / high
- interval
- probability distribution summary
- ensemble disagreement
- conformal set
- unknown / unavailable

Every representation should declare its semantics.

## Authority type

Authority records should identify:

```text
actor
principal
scope
capability / permission
policy_ref
policy_version
expiry / revocation
source of delegation
```

Authority must not be inferred from estimator fields.

For autonomous structural mutation, the authority record must additionally identify the versioned deterministic policy/classifier proving that the exact proposed change was within a delegated S0/S1 envelope.

## Decision-receipt type

A common receipt should support:

```text
decision_ref
decision_outcome
requested_action
state_snapshot
estimate_refs
policy_version
authority_refs
permitted_actions
prohibited_actions
selected_action
selection_mode
before_state
after_state
evidence_refs
rollback_or_recovery_ref
timestamp
```

The decision and receipt remain distinct artifacts. The receipt carries enough authority context to identify the decision and reconstruct its outcome class, while the referenced decision remains authoritative for the full PAMA evaluation record.

Decision-receipt version compatibility currently follows this boundary:

```text
1.0.0
  historical receipt shape
  decision_ref / decision_outcome absent or optional
  remains valid historical evidence

1.1.0
  decision_ref required
  decision_outcome required
  receipt <-> decision binding can be verified bidirectionally
```

This is intentionally versioned rather than retroactively making new fields required on all stored receipts. Optional-to-required evolution is breaking unless historical objects are migrated, and signed or content-addressed evidence must not be silently rewritten merely to satisfy a newer convenience contract.

For 1.1.0 receipts, consumers that possess the referenced decision should verify at least:

- `decision_ref` resolves to the intended PAMA/authority decision;
- `decision_outcome` matches that decision;
- policy version and permitted/prohibited action sets match;
- selected action matches the decision and belongs to the permitted set;
- the decision points back to the same receipt;
- the outcome and action envelope are internally consistent.

A receipt proves what was recorded about the authority decision and selected consequence. It does not, by itself, prove downstream execution occurred.

## PAMA-decision type evolution

The PAMA decision contract uses a closed operation enum because operation meaning is part of authority semantics, not decorative vocabulary. Adding a new operation therefore needs an explicit compatibility boundary even when the JSON shape is otherwise unchanged.

Current compatibility:

```text
1.0.0
  historical operation vocabulary
  remains valid historical evidence

1.1.0
  adds mutation.operation = decision_overwrite
  preserves all existing 1.0.0 operation meanings

1.2.0
  adds mutation.operation = domain_schema_mutation
  preserves 1.0.0 and 1.1.0 historical meanings
  domain schema mutation remains conservatively review-gated

1.3.0
  preserves historical 1.2.0 domain-schema decisions
  binds domain_schema_mutation to an exact ADR-032 structural-impact record
  permits only deterministically eligible S1 to use autonomous allow_with_ledger
  keeps S2/S3 review / external-verification / block floors
```

`decision_overwrite` is intentionally distinct from `correction`, `authority_change`, and `other`:

- `correction` can repair a decision record without changing what was decided;
- `authority_change` changes authority itself;
- `decision_overwrite` requests supersession/reversal of durable decision state under ADR-025;
- `other` must not be used to hide a known consequential mutation class merely to avoid schema evolution.

`domain_schema_mutation` is intentionally distinct from ordinary fact insertion, Agent Memory doctrine-core schema change, unchanged-semantic index rebuild, and policy mutation. It represents durable application/domain-model changes capable of altering future extraction, typing, relation meaning, migration, or recall.

Because new enum members and new authority semantics can break closed consumers, the producer/version boundary must match the operation and interpretation. A `decision_overwrite` record claiming 1.0.0 is invalid. A `domain_schema_mutation` record claiming a pre-1.2.0 version is invalid. A consumer that supports only 1.2.0 must explicitly reject a 1.3.0 structural decision rather than infer that its newer impact bindings are decorative.

Consumers performing consequential mutation must therefore treat an unsupported PAMA decision schema version or unknown operation as an explicit compatibility failure, not silently coerce it to a familiar action.

### Current PAMA structural posture

Historical PAMA 1.2 maps `domain_schema_mutation` conservatively:

```text
low / medium -> require_review
high / critical -> require_external_verification
```

PAMA 1.3 adds the first executable ADR-032 structural delegation profile. It does **not** make all additive changes autonomous.

The reference path is:

```text
structural proposal
  -> exact semantic/scope/dependency impact record
  -> deterministic S0-S3 classifier + versioned policy
  -> state/dependency freshness check
  -> common PAMA floors
  -> authority decision
```

S0 remains unchanged-semantic derived maintenance and is refused as `domain_schema_mutation`.

A bounded S1 application/domain extension may resolve to:

```text
outcome: allow_with_ledger
selection_mode: deterministic
```

only when the exact structural record satisfies the versioned S1 policy. The reference policy currently limits S1 to configured local/application/project scopes, a configured affected-memory bound, preserved semantics/history/isolation, no migration or information loss, no scope/authority widening, no incompatible dependencies, and an explicit rollback reference. Those reference-policy values are not universal doctrine thresholds.

S2 remains human-review required by default. S3 remains external-human or stricter and may be blocked by existing PAMA scope, M5/A5, isolation, reversibility, or other floors.

Authorization is bound to the exact state and dependency snapshot digests used by structural impact analysis. Drift invalidates the prior structural authorization. Estimator confidence, estimator disagreement, repetition, or prior autonomous success cannot lower the structural authority floor.

Canonical executable profile: [`profiles/pama-1-3-structural-delegation.md`](profiles/pama-1-3-structural-delegation.md).

## Migration

A migration should record:

```text
migration_id
from_schema_version
to_schema_version
transformation
lossy_fields
semantic_changes
validation_result
rollback_or_backup_ref
```

For durable runtime structural evolution also preserve relevant proposal, authority, dependency, module/projection rebuild, and residue evidence.

Lossy migration requires explicit handling. "The old field didn't fit" is not provenance.

A migration is not the same event as schema authorization, schema activation, rollback, supersession, or retirement. Those lifecycle states should remain distinguishable when consequence warrants it.

## Unknown fields and versions

For low-risk read-only consumers, preserving unknown extension fields may be sufficient.

For consequential mutation, a consumer should not silently process an unknown core schema version if it cannot establish the semantics required for authority.

Possible outcome:

```text
unsupported_schema -> abstain / quarantine / require_adapter
```

## Registry governance

Schema changes should be reviewed or deterministically classified for:

- backward compatibility
- semantic compatibility
- privacy impact
- scope/isolation impact
- authority impact
- deletion/migration impact
- dependent module/projection/consumer impact
- reversibility/rollback
- residue/rebuild obligations
- conformance impact
- implementation adoption cost

Probabilistic systems may supply evidence or recommendations for these dimensions. They may not directly mint canonical structural authority.

## Current repository schemas

The repository schema registry includes machine-readable contracts for memory units, conformance results, audit events, decision receipts, PAMA decisions, structural mutation impact, calibration evidence, source records, portable/interchange evidence, isolation boundaries, governance projections, and other bounded profiles introduced by validated architecture slices.

The canonical inventory is the [`../schemas/`](../schemas/) directory. Do not rely on a hand-maintained schema count in prose as a maturity signal.

Core examples include:

- [`../schemas/memory-unit.schema.json`](../schemas/memory-unit.schema.json) — the memory unit, including uncertainty, scope, tombstone, and action-envelope fields
- [`../schemas/conformance-report.schema.json`](../schemas/conformance-report.schema.json) — conformance results with estimator/policy versioning and the standardized metric family
- [`../schemas/memory-audit-event.schema.json`](../schemas/memory-audit-event.schema.json) — structured audit events with correlation/causation identifiers
- [`../schemas/decision-receipt.schema.json`](../schemas/decision-receipt.schema.json) — reconstruction receipts for consequential decisions, including the versioned authority-decision backlink
- [`../schemas/pama-decision.schema.json`](../schemas/pama-decision.schema.json) — PAMA authority decision records, with versioned closed-operation and structural-delegation evolution
- [`../schemas/structural-mutation-impact.schema.json`](../schemas/structural-mutation-impact.schema.json) — exact ADR-032 semantic/scope/dependency impact and deterministic S0-S3 classification evidence
- [`../schemas/calibration-results.schema.json`](../schemas/calibration-results.schema.json) — labeled calibration case input for the calibration report generator
- [`../schemas/source-record.schema.json`](../schemas/source-record.schema.json) — source-registry records with rights and reuse gating

## Fixture versioning

Conformance fixtures are versioned artifacts with their own evolution rules, distinct from the schemas of the objects they contain:

```text
"fixture_version": "MAJOR.MINOR.PATCH"
```

- The fixture version describes the **scenario contract**: expected behavior, required invariants, trap semantics, and material scenario inputs, not the memory-unit schema version.
- Prose or metadata changes that leave expected behavior untouched may remain patch-compatible.
- Changing expected behavior, required invariants, trap semantics, or material scenario inputs requires a version change; breaking scenario-semantic changes require a major version change.
- Runtime evidence must record `fixture_id` plus `fixture_version`, so results remain comparable after fixtures evolve.
- `scripts/validate_fixtures.py` requires and validates the field on every fixture.

## Conformance cases

- old consumer receives new optional field
- old consumer receives unknown enum member
- historical 1.0 PAMA decision remains valid
- `decision_overwrite` presented as PAMA decision 1.0 is rejected
- `domain_schema_mutation` presented as pre-1.2 PAMA decision is rejected
- 1.2-only consequential consumer receives PAMA 1.3 structural decision and rejects it explicitly
- unknown PAMA operation/schema attempts durable mutation
- historical 1.0 decision receipt remains valid under the compatibility schema
- 1.1 decision receipt omits required decision backlink/outcome
- decision receipt references the wrong authority decision
- decision receipt outcome does not match the referenced decision
- decision and receipt point at different counterparts
- outcome class contradicts the permitted/prohibited action envelope
- decision receipt references mismatched policy version
- estimator score changes semantics without type change
- migrated object loses provenance
- schema adapter strips tenant scope
- unknown schema attempts durable mutation
- high-confidence structural proposal cannot self-authorize
- bounded additive change cannot bypass deterministic S1 eligibility evidence
- repeated proposals cannot accumulate structural authority
- probabilistic estimator disagreement cannot become an implicit allow
- semantic migration cannot be mislabeled as derived rebuild
- stale structural impact analysis cannot authorize commit
- dependency drift cannot reuse stale structural authorization
- declared rollback must bind the authorized rollback reference and execution evidence
- retirement with live dependencies/residue cannot claim completion

## Related architecture

- [`42-governed-mutable-memory-fabric.md`](42-governed-mutable-memory-fabric.md)
- [`adr/ADR-032-governed-mutable-memory-structure.md`](adr/ADR-032-governed-mutable-memory-structure.md)
- [`profiles/pama-1-2-domain-schema-compatibility.md`](profiles/pama-1-2-domain-schema-compatibility.md)
- [`profiles/pama-1-3-structural-delegation.md`](profiles/pama-1-3-structural-delegation.md)
- [`explorations/memory-architectures/progressive-domain-schema-discovery.md`](explorations/memory-architectures/progressive-domain-schema-discovery.md)

## Doctrine

Schemas govern meaning, not merely syntax.

Interoperability is unsafe when two components agree on JSON while disagreeing on what the JSON means.

Structure may evolve, but a system that lets uncertain discovery silently rewrite canonical meaning has confused adaptation with authority.
