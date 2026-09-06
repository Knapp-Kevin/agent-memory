# Epistemic Belief Memory Reference

Status: **bounded runtime reference for issue #346**

Capability: `epistemic_belief_memory@1.0`

Component: `agent-memory-epistemic-reference@0.1.0`

## Purpose

Capability Contract v3 introduced an explicit retained-memory capability for claims, beliefs, hypotheses, confidence, supporting/contradicting evidence, and revision state. This reference makes that semantic boundary executable without creating a second memory engine or treating belief as fact.

The path is:

```text
claim / belief / hypothesis revision
        |
        v
stable belief identity + directional evidence
        |
        v
CognitiveSignal(module_role=epistemic_memory)
        |
        v
Cognitive Mesh
        |
        v
PAMA authority evaluation
        |
        +-- refused -> proposal evidence only
        |
        +-- committed -> append-only epistemic revision
        |
        v
governed recall
        |
        +-- active belief -> eligible active cognition
        +-- disputed belief -> retained, not active cognition
        +-- retracted belief -> historical only, no current claim
```

## Semantics

Each belief has one stable `belief_ref` and an append-only sequence of explicit `revision_ref` values. A revision records:

- epistemic kind: `claim`, `belief`, or `hypothesis`;
- claim text for active/disputed revisions;
- confidence when supplied;
- supporting evidence refs;
- contradicting evidence refs;
- prior revision ref;
- revision reason;
- governed scope/isolation/project/task/purpose;
- source component and optional estimator identity/version;
- epistemic status: `active`, `disputed`, or `retracted`.

Supporting and contradicting evidence are retained as separate directional sets. They are flattened only when the generic PAMA proposal requires an evidence list; the epistemic record does not erase which evidence supported or contradicted the claim.

## Revision and authority boundary

Initial retention uses the existing `promotion` operation. A later belief revision uses the existing `correction` operation, so the current PAMA correction policy remains controlling. Confidence is carried as estimator evidence and cannot satisfy review or external-verification requirements.

A refused correction is never appended to current epistemic state.

The reference also rejects stale lineage and silent scope movement before substrate mutation. A revision must extend the exact current revision and retain the same governed scope.

## Dispute and retraction

A disputed belief remains retained epistemic state but the epistemic recall layer removes it from active cognition with an explicit `epistemic_disputed` refusal. It is not relabeled as a fact simply because it was committed.

Retraction uses the existing governed `pruning` consequence. The prior fact remains historically attributable in the permissive substrate, but Agent Memory records a tombstone, clears the current recall fact, and appends a retraction revision with no replacement claim text. This avoids inventing a current pseudo-fact whose content is merely “this belief was retracted.”

## Capability maturity and operational honesty

The reference component declares:

```text
profile_version: component-capability-v3
maturity: runtime_wired
authority_effect: none
```

Its operational contract is intentionally process-local:

```text
write_atomicity: process_local
concurrency_control: process_local
idempotency: process_local
restart_recovery: process_local_only
reconciliation: process_local_only
```

That means this slice proves semantic composition and governance, not restart reconstruction or production substrate portability. Capability Contract v3 can later require stronger operational properties and exclude this reference provider when the operation demands them.

## Non-claims

This implementation does not:

- certify epistemic state as `semantic_fact_memory`;
- automatically derive confidence from evidence;
- treat confidence `1.0` as authority;
- implement predictive/counterfactual memory or world modeling;
- provide cross-process restart reconstruction;
- claim durable idempotency or reconciliation;
- add an external provider dependency;
- create a new PAMA authority class.

The next predictive/world-model slice should consume this distinction rather than collapse predicted outcomes, beliefs, and observed history into one record type.
