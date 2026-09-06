# ADR-010: Conflict Resolution Is a Separate Component

## Status

Accepted

## Context

The lifecycle state machine includes a `disputed` state. That state identifies a problem, but it does not resolve the problem.

Conflicts can arise between facts, decisions, time windows, scopes, policies, source reliability estimates, user corrections, estimator outputs, procedures, and implementation states.

If conflict handling is embedded ad hoc inside each implementation, the same dispute can produce incompatible consequences across systems.

## Decision

Conflict resolution is a separate architectural component or explicitly bounded component contract.

Conflict **interpretation** may be probabilistic. Detection, classification, source ranking, causal interpretation, and stale-versus-superseded analysis can remain uncertain.

Conflict **consequence** must be governed through explicit outcomes such as:

```text
retain_both
split_scope
mark_disputed
request_more_evidence
require_verification
correct_preserve_history
demote
archive_superseded
block_canonical_use
escalate
```

Canonical document:

- [`../17-conflict-resolution-engine.md`](../17-conflict-resolution-engine.md)

## Consequences

### Positive

- prevents silent overwrite
- preserves alternative hypotheses and historical truth
- allows temporal supersession without deleting valid history
- supports policy-aware reconciliation
- separates uncertain interpretation from authorized mutation

### Negative

- requires conflict taxonomy and evidence exposure
- requires policy for resolution outcomes
- may require review for high-risk unresolved disputes

## Acceptance scope

Accepted establishes conflict resolution as canonical architecture. It does not require deterministic conflict classification or claim one universal resolution algorithm.

## Doctrine

Dispute is a state.

Interpretation may be uncertain.

Resolution consequence is governed.
