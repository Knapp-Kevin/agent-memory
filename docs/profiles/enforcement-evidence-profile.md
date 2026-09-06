# Enforcement Evidence and Posture Profile

Status: reference V0.1 implementation profile for issue #152 Phase 3.

## Purpose

This profile closes the evidence gap between a governance decision and an observed enforcement/execution event.

```text
decision issued
!= decision delivered
!= enforcement point reached
!= action prevented / executed
```

The profile therefore adds two vendor-neutral surfaces:

- `execution-witness.schema.json` for a specific observed event bound to the exact composed decision identity;
- `enforcement-posture-report.schema.json` for machine-readable configured enforcement modes, witness coverage, liveness, and the evidence scope actually observed.

Neither surface changes Agent Memory memory semantics or PAMA authority.

## Execution witness

Reference implementation:

`reference/agentmem_ref/memory/enforcement_evidence.py`

A witness binds to:

```text
input_identity
composition_id
action_ref
witness_ref
effective_decision
enforcement_mode
delivery_status
enforcement_point_status
action_status
liveness_status
observed_at
```

The witness may report:

```text
enforcement_mode = mechanical | cooperative | unknown
delivery_status = delivered | failed | not_observed
enforcement_point_status = reached | unavailable | not_observed
action_status = executed | prevented | refused | unknown | not_observed
```

An action outcome cannot be claimed unless the enforcement point itself was observed.

A witness input identity that does not match the composed decision is rejected.

## Negative evidence is first-class

A runtime action that executes despite an effective `deny` is preserved as:

```text
effective_decision = deny
action_status = executed
decision_alignment = violation
```

It is not discarded as malformed evidence. The violation is the evidence.

For permitted actions, downstream prevention/refusal is represented as `stricter_than_decision`, because a downstream enforcement layer may narrow permission without widening it.

For `require_approval`, observed execution alone is `unverifiable`; this V0.1 witness does not infer that an approval reference is valid or correctly bound merely because execution occurred.

## Non-claims

Every execution witness explicitly preserves these limits:

```text
lifecycle_satisfaction_not_established
execution_witness_does_not_create_memory_authority
```

Execution evidence can show that an action occurred or was prevented. It does not prove correction completeness, forgetting, deletion closure, semantic authorization, or other lifecycle obligations.

## Enforcement posture

The posture report covers these surfaces independently:

```text
memory_write
recall_admission
background_maintenance
external_import
```

Each is:

```text
mechanical | cooperative | unknown
```

Execution-witness capability is recorded separately as:

```text
available | partial | absent
```

Liveness is:

```text
healthy | degraded | unavailable | unknown
```

Most importantly, configured governance is not reported as observed enforcement.

The report derives exactly one evidence scope:

```text
configuration_only
witness_capability_only
observed_enforcement
```

Examples:

```text
governance configured + no witness capability + zero witnesses
-> configuration_only

witness capability available + zero observed witnesses
-> witness_capability_only

one or more observed witnesses
-> observed_enforcement
```

This prevents a configured policy engine or SDK hook from being described as mechanically enforced merely because it exists.

## Adversarial fixture

Fixture:

`fixtures/enforcement-evidence-matrix.json`

Tests:

`reference/tests/test_enforcement_evidence.py`

The V0.1 set covers:

- deny + mechanical prevention;
- deny + observed execution violation;
- allow + execution;
- allow + stricter downstream prevention;
- approval-required + execution without approval verification;
- decision delivered while the enforcement point remains unobserved;
- configured governance with enforcement/witness absent;
- witness capability present without an observed event;
- observed enforcement posture;
- action-identity mismatch;
- impossible action-outcome overclaim without an observed enforcement point.

## Relationship to decision composition

This profile consumes the existing decision-composition receipt created by the #152 Phase 1 V0.1 seam.

The composed decision remains immutable decision evidence. Execution evidence is a separate artifact bound back to the composition identity and exact `input_identity`.

That separation prevents later runtime observations from rewriting what the original policy decision claimed.

## What V0.1 proves

Within the bounded fixture set, the profile demonstrates that:

- action identity remains bound through execution evidence;
- decision delivery is separate from enforcement-point observation;
- cooperative, mechanical, and unknown enforcement modes are representable;
- configured governance without observed enforcement stays `configuration_only`;
- downstream execution despite deny is visible as a violation;
- a witness cannot overclaim action execution/prevention when the enforcement point was not observed;
- execution evidence does not imply lifecycle satisfaction.

## What V0.1 does not prove

This slice does not prove:

- that every host intercept path is mechanically complete;
- production liveness monitoring;
- approval validity or approval-authority continuity;
- physical-world completion;
- lifecycle obligation satisfaction;
- correctness of a third-party enforcement product;
- AGT, DashClaw, OPA, Cedar, or other peer-specific interoperability.

Those remain separate evidence or comparator slices.
