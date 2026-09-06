# Reusable grant authority-transition profile

**Status:** Reference implementation V0.1  
**Issue:** #250  
**Parent:** #153  
**Research basis:** #172

## Purpose

This profile separates historical decision evidence from reusable authority.
Repeated materially equivalent independent human decisions may justify an
**advisory proposal** for a narrow reusable grant. The proposal itself has no
authority. A grant exists only after a separate, explicitly evidenced and
independently verified ratification transition.

```text
historical decision evidence
  -> deterministic precedent applicability
  -> non-authoritative grant proposal
  -> explicit ratification
  -> scoped reusable review grant
```

The following states remain distinct:

```text
history
!= one-action approval
!= grant proposal
!= ratified reusable grant
!= autonomy policy
```

## Existing boundaries preserved

- `precedent_applicability.py` remains advisory and unchanged.
- `approval_evidence.py` remains one-action evidence with `reusable_authority: false`.
- estimator-mediated retrieval remains candidate discovery only.
- PAMA remains the final Agent Memory consequence envelope.

A current reusable grant may discharge only an ordinary PAMA `require_review`
result. It cannot discharge `require_external_verification`, override `block`,
widen scope, change operation, or create an autonomy policy.

## Proposal eligibility

A V0.1 proposal requires deterministic precedent applicability, same governed
scope, review-reduction-safe applicability, no relevant negative precedent,
no material mismatch or unknown condition, no stale/invalid supporting state,
and at least two unique current independent-human adjudication source refs.

The implementation deliberately deduplicates human evidence by provenance
`source_ref`. Multiple memories or projections derived from one adjudication do
not become multiple independent human decisions.

Proposal output binds:

- source projection and applicability identity;
- requested operation;
- exact scope refs;
- current material-condition values;
- policy version;
- requested validity window;
- revocation mechanism;
- unique supporting human decision and memory refs.

Every proposal records `authority_effect: none`, `can_authorize_execution: false`,
`can_self_ratify: false`, and `can_create_autonomy_policy: false`.

## Ratification

Ratification is a separate authority transition. It requires a new ratification
reference, ratifying principal, independently verified ratifier-authority
evidence, exact operation/scope/material-condition/policy binding, issuance and
expiry, and the same revocation mechanism proposed originally.

Ratification may narrow a proposal but V0.1 does not permit it to widen or alter
operation, scope, material conditions, policy version, or requested validity.
A historical decision ref cannot be reused as the ratification event.

## Currentness and revocation

A reusable grant is usable only when re-evaluation confirms:

- the ratification evidence is still present;
- the grant is issued and unexpired;
- no matching revocation is effective;
- policy version is unchanged;
- operation and scope still match exactly;
- deterministic precedent applicability remains review-reduction-safe;
- no relevant negative/incident precedent is current;
- material-condition values still match the ratified grant.

Any failure produces `not_applicable`, `stale`, `revoked`, or `invalid`, with
`satisfies_reusable_approval: false`.

## Feedback-loop protection

Execution under a grant is classified as `policy_outcome` provenance with
`independent_adjudication: false`. It therefore cannot recursively increase the
independent-human count that motivated the grant.

The profile also proves that duplicated representations of one human decision
remain one unique adjudication for grant-proposal purposes.

## PAMA composition

The helper first computes PAMA without the grant. Only if the baseline outcome is
exactly `require_review`, the grant evaluation is current, operation matches, and
scope is bound may the grant supply the external approval reference used to
re-evaluate PAMA.

`require_external_verification` and `block` remain absorbing. This makes reusable
authority a bounded review transition rather than a shortcut around PAMA.

## Evidence

The focused harness includes 12 adversarial scenarios covering safe proposal and
ratification, policy-derived repetition, negative precedent, cross-scope reuse,
material change, policy drift, expiry, revocation, reused-grant attribution,
PAMA widening, and missing ratification evidence. A separate duplicate-history
case tests self-corroboration resistance.

Metrics separate successful bounded review discharge from unsafe activations,
authority-transition failures, attribution errors, PAMA widening, and recursive
authority inflation.

## Non-goals

This profile does not implement automatic policy mutation, self-ratifying grants,
broad action-class allowlists, cross-tenant or cross-agent authority sharing,
general autonomy policies, or production interruption optimization. External
peer vocabularies remain comparator evidence rather than core Agent Memory
ontology.
