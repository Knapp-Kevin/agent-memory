# Exact-Identity Approval Evidence Profile

Status: reference V0.1 implementation profile for issue #187 and the remaining approval-continuity boundary in #152.

## Purpose

This profile records and verifies a one-action approval decision without turning approval history into reusable authority.

```text
approval for action/state A
!= approval for action/state B

approval evidence
!= standing grant

approval recorded
!= action executed
```

The approval artifact sits between decision composition and execution evidence:

```text
Agent Memory / external decision composition
        |
        v
require_approval
        |
        v
one-action approval evidence
        |
        v
approval verification against exact identity/current state
        |
        v
execution witness
```

Each layer remains independently reconstructable.

## Contracts

Approval evidence schema:

`schemas/approval-evidence.schema.json`

Verification result schema:

`schemas/approval-verification-result.schema.json`

Reference implementation:

`reference/agentmem_ref/memory/approval_evidence.py`

Execution integration:

`reference/agentmem_ref/memory/enforcement_evidence.py`

## Approval evidence

The V0.1 artifact binds:

- exact `input_identity`;
- exact `composition_id`;
- approving principal reference;
- authority-evidence reference;
- scope reference;
- outcome (`approved`, `denied`, `revoked`);
- approval mechanism/host reference;
- issuance time;
- optional expiry;
- optional revocation time/evidence;
- supporting evidence references.

`reusable_authority` is fixed to `false`.

A future standing grant, reusable approval, or autonomy-policy transition must be a separate governed authority artifact under #172/#153. Repetition of these records cannot self-ratify such a transition.

## Verification

Approval verification checks the artifact against the current decision composition and observation context.

Possible states are:

```text
current
denied
stale
invalid
not_applicable
```

Only:

```text
status = current
satisfies_required_approval = true
```

may satisfy a `require_approval` composition.

Exact identity and scope mismatches are invalid. Expired/revoked approvals are stale. A denied approval is unsatisfied. An approval presented against `deny`, `allow`, or `warn` is `not_applicable`, because approval is not a generic bearer token that changes the underlying decision.

## Execution witness integration

Execution witnesses now report one of:

```text
absent
unverified
verified_current
stale
denied
invalid
not_applicable
```

A bare `approval_evidence_ref` remains `unverified`.

For an effective `require_approval` decision:

```text
executed + verified_current approval -> consistent
executed + bare/stale/denied/invalid approval -> unverifiable
prevented/refused -> consistent
```

For an effective `deny`, even a valid approval artifact cannot widen authority:

```text
deny + approved evidence + executed -> violation
```

## Replay resistance

The approval binds to the same deterministic `input_identity` used by the composition boundary. If proposal state, action identity, scope-bound inputs, or PAMA authority state changes such that `input_identity` changes, the prior approval cannot satisfy the new action.

The execution witness also rejects an approval-verification result whose input/composition identity belongs to another decision.

## Adversarial evidence

Fixture:

`fixtures/approval-evidence-matrix.json`

Tests:

`reference/tests/test_approval_evidence.py`

The bounded V0.1 set covers:

- current approved exact identity;
- expiry;
- revocation;
- denial;
- wrong input identity;
- wrong composition identity;
- approval presented against an effective deny;
- state-change replay;
- bare approval reference remaining unverified;
- verified approval satisfying `require_approval` execution;
- execution witness rejecting verification from a different composition.

## Non-claims

This profile does not prove:

- that an approver should have been authorized merely because an authority reference exists;
- production identity-provider validation;
- reusable/standing authority;
- execution merely because approval occurred;
- lifecycle satisfaction;
- remote approval UX or delivery guarantees.

It proves only the bounded identity/current-state continuity represented and executed by the reference tests.
