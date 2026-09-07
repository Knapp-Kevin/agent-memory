# Lifecycle State Machine

## Purpose

The lifecycle state machine defines how agentic memory moves from raw experience to durable memory, correction, or pruning.

The state machine does not assume every memory should become permanent. Most memory should remain operational, decay naturally, or be pruned.

The state machine also separates **transition proposal** from **transition commit**. Probabilistic, learned, heuristic, or model-directed components may propose that a memory should move. Only an authorized and valid lifecycle operation may commit the state change.

## Canonical states

```text
Transient
  -> Observed
  -> Linked
  -> Reinforced
  -> Candidate
  -> Pending Verification
  -> Crystallized
  -> Operationally Reused
  -> Stale
  -> Disputed
  -> Corrected
  -> Reconciled
  -> Pruned
```

## State definitions

### Transient

Short-lived memory used for immediate context. Usually lives in a fast cache or session context.

Entry conditions:

- user message
- tool response
- runtime trace
- temporary reasoning artifact
- unverified observation

Exit conditions:

- ignored and allowed to expire
- promoted to Observed
- attached to an existing memory unit

### Observed

A memory unit exists because some observer recorded an artifact or relation.

Required metadata:

- observer
- timestamp
- source
- method
- raw reference or content hash

### Linked

The memory has graph relations to other memory units.

Example links:

- supports
- contradicts
- depends_on
- refines
- replaces
- derived_from
- implements
- mentions

### Reinforced

The memory has additional support through use, corroboration, cross-reference, verification, or repeated relevance.

Reinforcement must distinguish between meaningful recurrence and access-spam.

### Candidate

The memory has sufficient saturation or governance relevance to be considered for durable treatment.

Candidate status is not approval.

A probabilistic or learned component may nominate Candidate state, but nomination must preserve its estimator output and must still pass transition validity and governance checks.

### Pending Verification

The memory is waiting on certification, approval, external confirmation, policy review, or test evidence.

Pending verification is the default state for high-impact memories that appear useful but are not yet trusted.

It is also a valid abstention state when the system cannot safely resolve uncertainty near a consequential boundary.

### Crystallized

The memory has passed identity, provenance, saturation, PAMA authority, and certification gates within a defined scope.

Crystallized does not mean eternal. It means durable under current evidence and policy.

### Operationally Reused

The memory is used by agents or workflows after crystallization or high-confidence routing.

Reuse must preserve references to provenance and certification.

### Stale

The memory remains available but its relevance or correctness may be degrading.

Staleness triggers may include:

- time decay
- changed project state
- changed user preference
- new contradictory evidence
- stale dependencies
- expired certification
- estimator drift that makes the prior lifecycle decision unreliable

### Disputed

The memory has been challenged by contradiction, failed verification, conflict, user correction, or policy change.

Disputed memories must not be silently used as canonical truth.

### Corrected

A dispute has produced a replacement or amendment.

Correction must preserve the old record and its dispute path.

### Reconciled

The corrected memory has been incorporated into the active graph or runtime state.

Reconciliation may result in:

- restored durable state
- downgraded operational state
- split scope
- pruned obsolete version

### Pruned

The memory has been removed from active recall or durable lifecycle consideration.

Pruned does not always mean deleted. Depending on policy, it may mean archived, tombstoned, summarized, or made inaccessible to normal retrieval.

## Transition proposal versus transition commit

A lifecycle implementation should model these as distinct operations.

```text
probabilistic / learned estimator
        |
        v
transition proposal
  proposed_state
  confidence / score
  estimator identity + version
  evidence refs
        |
        v
transition validation
  legal from current state?
  scope valid?
  authority sufficient?
  policy permits consequence?
  uncertainty acceptable for consequence class?
        |
        +--> block
        +--> abstain / Pending Verification
        +--> require review
        +--> permit
        |
        v
transition commit
  deterministic or formally bounded state mutation
  audit receipt
```

Rules:

1. A proposal does not mutate lifecycle state.
2. An estimator cannot authorize its own proposed transition.
3. For a fixed current state, policy snapshot, authority record, and committed inputs, transition validity must be reproducible or formally bounded.
4. A blocked transition must not become allowed because a model repeats it with greater confidence.
5. If multiple permitted transitions remain, deterministic or stochastic selection may occur only within that permitted set.

## Required transition metadata

Every committed state transition should record:

```text
from_state
to_state
trigger
authority
actor
timestamp
evidence_refs
policy_refs
policy_version
confidence_before
confidence_after
saturation_before
saturation_after
estimator_refs
estimator_versions
uncertainty_summary
proposal_ref
ledger_ref
```

Where applicable, `uncertainty_summary` should identify whether the relevant estimate was well calibrated, near a decision boundary, in disagreement with another estimator, or outside its validated scope.

## Promotion gates

A memory can move from Candidate to Pending Verification only if:

```text
identity_resolved == true
provenance_present == true
saturation >= candidate_threshold
trap_class_check != fail
pama_authority in [allow, require_review]
```

This expression is a minimum gate, not a claim that scalar thresholds are sufficient.

If saturation, confidence, trust, sensitivity, or contradiction estimators are uncertain near a consequential boundary, policy may require:

```text
abstain
require_review
require_external_verification
collect_more_evidence
```

rather than treating tiny score changes as authoritative state changes.

A memory can move from Pending Verification to Crystallized only if:

```text
certification_gate == pass
pama_authority == allow
scope_defined == true
dispute_status == clear
```

Crystallization must bind to the policy version and evidence/estimator context used to authorize it.

## Threshold stability and hysteresis

Lifecycle systems should avoid oscillating memory states because an uncertain score moves slightly above or below a threshold.

Where repeated boundary crossings are plausible, implementations should consider:

- separate enter and exit thresholds
- minimum evidence changes before reversal
- cooldown or observation windows
- explicit dispute/review states instead of rapid promotion/demotion
- confidence intervals or calibrated uncertainty around the score

Example:

```text
candidate_enter_threshold = 0.80
candidate_exit_threshold  = 0.70
```

The specific values must be calibrated. The doctrine requirement is stability proportional to consequence, not those numbers.

## Demotion gates

A crystallized memory should be demoted when:

- certification expires
- contradiction is introduced
- policy scope changes
- source is invalidated
- user correction overrides previous state
- implementation dependency changes
- estimator calibration or provenance is invalidated in a way that undermines the original promotion basis

Demotion should move to Stale, Disputed, or Corrected, not directly to deletion.

## Trap-class handling

### Access-spam junk

A low-value memory repeatedly accessed must not automatically become durable.

Required behavior:

- access alone has low pinning weight
- cross-reference and corroboration matter more than raw reads
- repeated access without external support should plateau below crystallization

### Confidently-wrong memory

A memory strongly reinforced but later proven wrong must not remain durable.

Required behavior:

- contradiction injects entropy
- saturation decreases
- dispute state blocks canonical use
- correction path preserves previous false claim for audit

### Threshold-jitter memory

A memory whose estimated lifecycle score repeatedly crosses a boundary because of estimator noise.

Required behavior:

- the system does not repeatedly promote and demote solely from tiny score changes
- decision-boundary instability is recorded
- consequential transitions use hysteresis, abstention, review, or additional evidence as policy requires

### Estimator-disagreement memory

Two valid estimators materially disagree about confidence, sensitivity, trust, or persistence value.

Required behavior:

- disagreement remains visible
- policy determines whether to combine, choose, abstain, or escalate
- no estimator gains authority merely by reporting a larger number

## Lifecycle goal

The lifecycle exists to make agent memory accountable.

A memory system is not mature because it remembers more. It is mature when it can explain why something was remembered, why it was trusted, why it changed, why uncertainty was tolerated or escalated, and why it was forgotten.
