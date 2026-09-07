# Integration Roadmap

## Purpose

This roadmap turns the doctrine into implementation work across related repos and native Agent Memory contracts.

The priority is consolidation before expansion. The system already has enough ideas. What it needs now is shared vocabulary, conformance boundaries, implementation hooks, and evidence that uncertain inference cannot silently become memory authority.

PAMA is native Agent Memory doctrine. Related repositories implement or consume doctrine; they do not define PAMA's provenance.

## Phase 1: Canonical doctrine stabilization

### Goal

Make this repository the shared reference point.

### Tasks

- finalize glossary
- finalize layer model
- finalize lifecycle state machine
- finalize scoring and decay doctrine
- finalize native PAMA governance boundaries
- finalize governed-uncertainty doctrine and disposition ADR-020 only after evidence supports acceptance
- finalize ADR set
- add source backlinks to related implementation repos where they add concrete value

### Exit criteria

```text
README points to canonical docs
ADRs accepted, revised, or explicitly proposed
native doctrine has canonical internal entry points
each materially relevant implementation repo has an implementation-map entry
open questions are tracked as issues
governed-uncertainty audit has no unresolved critical contradiction
```

## Phase 2: Cross-repo backlinks

### Goal

Every materially relevant implementation repo references the doctrine.

### Target repos

- UOR Framework
- EvolveAI
- CodeGenome
- COREFORGE / successor runtime as applicable
- FailSafe or governance implementations as applicable

A repository is not a backlink target merely because it is adjacent to Agent Memory concepts. It should map a concrete implementation responsibility or conformance surface.

### Recommended backlink text

```text
This implementation follows the Agent Memory doctrine maintained in MythologIQ-Labs-LLC/agent-memory. See the layer model, lifecycle state machine, PAMA governance model, governed-uncertainty doctrine, and conformance test plan for canonical terminology.
```

## Phase 3: Implementation alignment issues

### Goal

Create repo-specific issues that map existing implementation behavior to doctrine.

### Suggested issues

1. Map UOR identity boundaries to ADR-001 and deterministic-substrate requirements.
2. Map EvolveAI lifecycle states to `docs/02-lifecycle-state-machine.md`, including proposal versus commit.
3. Map EvolveAI CMHL and MTS logic to `docs/03-scoring-and-decay.md`, including estimator version, calibration scope, uncertainty, hysteresis, and drift.
4. Map CodeGenome confidence and provenance to the evidence layer, including inferred-edge estimator provenance and disagreement.
5. Map COREFORGE Vault writes to PAMA enforcement points.
6. Map Neurospace runtime memory to operational versus canonical memory states and recall-time scope enforcement.
7. Map FailSafe / Arbiter approval gates to crystallization and mutation transitions, including policy-version and permitted-action receipts.
8. Map a real durable-decision implementation to [`profiles/durable-decision-memory-profile.md`](profiles/durable-decision-memory-profile.md) only when implementation evidence is available.

## Phase 4: Governed-uncertainty boundary inventory

### Goal

Identify every place an estimate can influence a consequential memory action.

### Required inventory fields

```text
component
estimator_or_rule
input_scope
output_type
estimator_version
calibration_scope
consequence_candidate
governance_boundary
policy_owner
permitted_action_set
commit_boundary
audit_receipt
```

### Exit criteria

- every probabilistic or learned estimator with memory consequences is listed
- every listed estimator points to a policy boundary
- every policy boundary points to a commit/enforcement point
- no estimator is documented as self-authorizing mutation, promotion, deletion, sharing, or certification

## Phase 5: Conformance fixture design

### Goal

Create executable fixtures for testing doctrine alignment.

### Core fixture set

- valuable persistent memory
- ephemeral memory
- access-spam junk
- confidently-wrong memory
- contradicted memory
- certified durable memory
- unauthorized mutation attempt
- pruning with audit preservation

### Governed-uncertainty fixture set

- high-confidence false promotion
- threshold jitter
- estimator disagreement
- cross-tenant relevance trap
- stochastic retrieval inside policy envelope
- unsafe multi-memory composition
- uncertain sensitivity classification
- irreversible deletion under uncertain utility
- policy-versus-estimator version drift
- concurrent conflicting mutation

### Deliverables

```text
fixtures/*.json
schemas/memory-unit.schema.json
schemas/conformance-report.schema.json
scripts/validate-fixtures.*
```

## Phase 6: Runtime enforcement hooks

### Goal

Make doctrine enforceable in product and agent runtimes.

### Target enforcement points

- Vault write boundary
- graph mutation boundary
- crystallization gate
- context assembly pipeline
- correction workflow
- pruning workflow
- deletion workflow
- scope-sharing / tenancy boundary
- agent action planner
- reusable capability authority boundary

### Required behavior

At each enforcement point, identify:

```text
PAMA target class M0-M5
lifecycle strength
requested operation
requested downstream authority A0-A5
what may be probabilistic
what must remain invariant
what policy version applies
what action set is permitted
what happens on missing authority
what receipt is emitted
```

## Phase 7: Calibration and uncertainty harness

### Goal

Calibrate lifecycle estimators and expose false-permanence, boundary-instability, and drift risk.

### Required metrics where applicable

```text
threshold
sample_size
persist_retention_rate
false_permanence_rate
evaporation_rate_for_true_ephemeral
trap_class_failure_rate
durability_dimensions_tested
scope_of_validity
calibration_error
boundary_instability_rate
abstention_rate
estimator_disagreement_rate
out_of_scope_rate
estimator_version
calibration_version
```

### Required studies

- threshold sensitivity
- perturbation stability
- repeated-seed behavior for stochastic components
- calibration by memory class and consequence class
- out-of-distribution behavior
- policy-version versus estimator-version change
- hysteresis or equivalent anti-oscillation behavior

## Phase 8: Decision receipts and replay

### Goal

Make consequential memory decisions reconstructable without requiring exact replay of stochastic cognition.

### Minimum receipt

```text
actor
memory_id
PAMA target class
lifecycle strength
requested_action
requested_downstream_authority
estimator_refs
estimator_versions
uncertainty_summary
policy_refs
policy_version
permitted_action_set
selected_action
selection_mode
before_state
after_state
rollback_path
evidence_refs
timestamp
```

### Exit criteria

An auditor can reconstruct what was estimated, what was allowed, what was prohibited, what was selected, and what changed.

## Phase 9: Research challenge loop

### Goal

Continuously test doctrine assumptions against accessible research and empirical failures.

### Practice

- prefer freely inspectable research where practical
- record findings that support the doctrine
- record findings that challenge it
- classify biological/cognitive transfers as mechanism, functional analogy, engineering prescription, or open hypothesis
- create conformance fixtures when research exposes a falsifiable failure mode
- do not promote a research-inspired idea to doctrine solely because the analogy is appealing
- keep external evidence separate from native doctrine authorship

## Phase 10: Doctrine versioning

### Goal

Make doctrine changes traceable.

### Proposed versioning

```text
v0.1: initial doctrine spine
v0.2: schema and fixture definitions
v0.3: executable conformance harness
v0.4: cross-repo implementation mappings
v0.5: governed-uncertainty receipts and runtime boundary inventory
v1.0: stable doctrine with tests, research challenge history, and adoption notes
```

## Cross-cutting implementation track: Governance Projection

### Goal

Allow governance, approval, and enforcement systems to consume useful Agent Memory context without reshaping the canonical memory model around any one consumer.

Canonical layering:

```text
Agent Memory core
  -> Governance Context Projection
  -> consumer-specific adapter
  -> governance / approval / enforcement runtime
```

The core remembers generally valuable state. The Governance Context Projection is derived, minimized, reconstructable context. Consumer adapters own consumer-specific policy vocabulary, risk semantics, API compatibility, and verdict mapping.

### Architectural rule

> Adapter convenience must not redefine canonical memory semantics.

When an integration needs a new field, first determine whether it exposes a generally useful missing memory primitive or merely a consumer-specific concept. Add only the former to core. Keep the latter downstream.

### V0.1: contract and deterministic fixtures

Tracked by #154 and proposed ADR-029.

- [ ] define the vendor-neutral governance-context projection profile
- [ ] add `schemas/governance-context-projection.schema.json`
- [ ] add exact/material-condition precedent fixtures
- [ ] preserve positive and negative precedent independently
- [ ] preserve scope, validity, provenance, outcome, and derivation metadata
- [ ] make the schema structurally exclude final consumer verdict/permission fields
- [ ] validate that policy-generated outcomes cannot masquerade as independent human adjudication

### V0.2: reference projection builder

- [ ] implement a deterministic builder over existing canonical memory primitives
- [ ] prove projection state can be discarded and rebuilt from canonical memory + evidence
- [ ] emit material-difference reports before adding semantic similarity
- [ ] keep sensitive raw content out of the projection when structured characteristics/references suffice
- [ ] add cross-scope and stale-precedent negative tests

### V0.3: estimator-mediated precedent retrieval

Only after deterministic matching is stable:

- [ ] define an estimator interface for semantic/contextual precedent candidate retrieval
- [ ] preserve estimator identity/version/calibration/uncertainty
- [ ] require deterministic governance consequence after estimator output
- [ ] test superficially similar but materially unsafe near-matches
- [ ] measure unsafe-equivalence false positives separately from interruption reduction

### V0.4: consumer adapters

- [ ] implement a generic fake governance consumer first
- [ ] evaluate a DashClaw-specific adapter without moving DashClaw fields into core
- [ ] evaluate an AGT/ACS-style adapter independently
- [ ] record rejected mappings and incompatibilities rather than forcing equivalence
- [ ] keep each consumer adapter optional and independently versioned

### V0.5: closed-loop evidence without authority laundering

- [ ] correlate decision context with downstream approval/enforcement evidence
- [ ] preserve whether an outcome came from independent human adjudication, policy, or runtime behavior
- [ ] permit repeated contextual precedent to propose a narrow policy/grant
- [ ] require a separate explicit authority transition before that proposal reduces review requirements
- [ ] prevent policy-generated allows from recursively becoming corroborating human precedent

### Exit criteria

```text
canonical memory schema remains consumer-neutral
projection is reconstructable derived state
projection carries no final consumer permission/verdict
scope and negative precedent survive projection
consumer adapters can evolve without redefining core memory
at least one real consumer demonstrates useful decision context
approval-friction reduction is measured alongside unsafe-equivalence failures
```

## Immediate next issues

Create or execute issues for:

1. Add schemas for memory units and conformance reports.
2. Add fixture examples for all required conformance cases.
3. Expand the calibration harness to measure uncertainty, drift, and decision-boundary stability.
4. Add cross-repo backlink and governed-uncertainty mapping issues only for implementation systems with concrete evidence value.
5. Add PAMA decision-table tests for M0-M5 target classes, A0-A5 authority ceilings, finite authority outcomes, and bounded stochastic action.
6. Add a decision-receipt schema that separates estimator outputs from governance outcomes.
7. Build the cross-repo boundary inventory before accepting ADR-020.
8. Validate at least one real implementation against the durable-decision memory profile rather than assigning doctrine provenance to an adjacent product.
9. Execute #154 to establish Governance Projection V0.1 before building any consumer-specific governance adapter.

## Acceptance dependency for ADR-020

ADR-020 should remain Proposed until at least the following are demonstrated:

```text
core conformance fixtures exist
governed-uncertainty fixtures exist
at least one implementation boundary is mapped end to end
high-confidence false promotion is blocked
cross-scope relevance is blocked at read time
stochastic choice cannot select prohibited actions
irreversible deletion is not authorized by utility score alone
policy and estimator version drift remain distinguishable
```

## Roadmap principle

Do not add another concept until the existing concepts have a stable place to live.

Do not add another implementation name until it earns a distinct role through evidence.

Do not call governed uncertainty complete until it survives implementation and adversarial testing. Documentation agreeing with itself is useful. It is also an exceptionally low bar for reality.
