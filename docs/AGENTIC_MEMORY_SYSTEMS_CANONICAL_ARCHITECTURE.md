# Agentic Memory Systems Canonical Architecture

## Purpose

This document defines the canonical architecture for governed agentic memory systems. It combines native Agent Memory doctrine with clearly bounded implementation and provenance relationships across UOR, EvolveAI, CodeGenome, COREFORGE Vault / Neurospace, FailSafe / Arbiter, and future conforming systems.

**PAMA is native Agent Memory doctrine authored by Kevin R. Knapp.** It is part of the canonical architecture itself, not another external system in the implementation list.

This document consolidates the logic into one doctrine so implementations can stop rediscovering the same boundary decisions under different names.

## Core thesis

Agentic memory is not retrieval.

Agentic memory is retained state that can alter an agent's future interpretation, reasoning, planning, tool use, action, or adaptation across a meaningful persistence boundary.

The architecture governs encoding, persistence, recall, revision, forgetting, sharing, inheritance, and mutation authority rather than treating retrieval as the whole system.

## Canonical pipeline

```text
Raw experience / artifact
        |
        v
Identity substrate
What is it? Can it be addressed deterministically?
        |
        v
Evidence layer
Who observed it? What supports it? What uncertainty applies?
        |
        v
Lifecycle / saturation layer
Should it persist, decay, route, recheck, consolidate, or become a promotion candidate?
        |
        v
PAMA governance layer
What is the M0-M5 target class, lifecycle strength, operation, and A0-A5 authority ceiling?
What consequences are permitted, blocked, deferred, or review-required?
        |
        v
Certification / crystallization gate
If durable canonical state is requested, have required verification and authority gates passed?
        |
        v
Runtime memory / governed recall
How may eligible memory influence this agent and task now?
```

## Layer model

| Layer | Question answered | Canonical responsibility |
|---|---|---|
| Identity | What is this object? | Deterministic content address, exact identity, object resolution |
| Evidence | Why do we believe this object or relation exists? | Provenance, witness material, uncertainty, observation records |
| Saturation / scoring | How much persistence or routing pressure exists? | Calibrated scoring, routing, decay, lifecycle candidacy |
| Lifecycle | What state is this memory in? | State transitions, decay, dispute, correction, pruning, promotion candidacy |
| **PAMA** | What adaptive consequence is permitted? | Native mutation target classes, authority ceilings, charters, proportional governance |
| Certification | Can this proposed durable transition be confirmed? | Verification, approval, integrity checks, certificate gates |
| Runtime memory | How is this memory used? | Operational storage, context assembly, graph recall, agent access |
| Governed recall | What retained state may enter active context? | Relevance plus scope, sensitivity, tenancy, dispute, certification, policy admission |
| Reality graphs | What structured domain relationships exist? | Domain graph evidence, confidence, provenance, impact traversal |
| Durable decision memory | How do decisions retain rationale and evolve safely? | decision state, supersession, drift evidence, rationale preservation |

## PAMA native doctrine

PAMA means **Proportional Adaptive Mutation Authority**.

Canonical foundation: [`pama/README.md`](pama/README.md).

PAMA preserves:

```text
adaptation != authority
memory != procedure
procedure != permission
permission != governance
```

Foundational dimensions include:

- **M0-M5 target classes**: what kind of state is being changed;
- **lifecycle strength**: how established the retained adaptive state is;
- **requested operation**: what transition or mutation is being attempted;
- **A0-A5 downstream authority**: what the state may influence;
- **adaptive charter**: what the proposing agent is allowed to learn or propose;
- **evidence and reversibility**: what supports the mutation and how safely it can be undone;
- **policy outcome**: what is allowed, ledgered, review-required, externally verified, or blocked.

A validated capability does not acquire external-action authority merely because it works reliably.

## Governing invariants

1. Identity is not memory.
2. Saturation is not truth.
3. Repetition is not durability.
4. Retrieval frequency is not permission to crystallize.
5. Crystallization is a governed transition, not a natural reward.
6. Certification confirms a required gate; it does not create eternal truth.
7. Provenance must survive summarization and derivation.
8. A memory that cannot be disputed or corrected cannot be safely canonical.
9. Mutation authority must be explicit and scoped.
10. Runtime usefulness does not imply canonical permanence.
11. Adaptation is not authority.
12. Memory is not procedure.
13. Procedure is not permission.
14. Permission is not governance.
15. Reliability does not expand a capability's authority ceiling.
16. Probability may inform authority; probability does not create permission.

## Memory state machine

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
  -> Archived / Pruned / Tombstoned
```

Not all memories move through every state. The state machine exists to make consequential transitions explainable.

PAMA lifecycle strength (`Observed`, `Tentative`, `Reinforced`, `Promoted`, `Canonical`) is a governance-facing abstraction over adaptive strength and must not be confused with every implementation lifecycle state. Mappings between the two should be explicit where used.

## Memory object model

A canonical memory object should carry, where applicable:

```text
id: stable identity pointer
content_ref: pointer to raw or canonical content
type: observation | decision | fact | trace | code_artifact | preference | policy | failure | correction
evidence: list of evidence records
provenance: origin, observer, timestamp, method
confidence / uncertainty: evidence-level epistemic state
saturation: calibrated lifecycle pressure
state: lifecycle state
pama_target_class: M0-M5 when mutation authority is evaluated
downstream_authority: A0-A5 ceiling when applicable
authority: mutation and promotion authority scope
certification: optional confirmation record
decay_profile: half-life, pressure, last access, dispute status
ledger_ref: audit or history pointer
```

## Distinction between confidence, saturation, authority, and certification

| Signal | Means | Does not mean |
|---|---|---|
| Confidence / uncertainty | Evidence supports an estimate to some degree | The memory should persist forever |
| Saturation | Memory has lifecycle relevance or persistence pressure | The memory is correct |
| PAMA authority | Policy permits a bounded consequence | The underlying claim is factually true |
| Certification | A verification or approval gate was satisfied | The memory can never be revised |

This distinction is mandatory. Collapsing these signals creates hallucination permanence and permission laundering.

## Crystallization rule

A memory may be crystallized only when all required gates pass:

```text
identity_resolved == true
provenance_present == true
saturation >= calibrated_threshold
trap_class_check == pass
pama_outcome permits crystallization
certification_gate == pass
scope_defined == true
dispute_status == clear
```

A high saturation score may propose crystallization. It must not grant crystallization by itself.

## Related implementation doctrine

External or related systems may map to portions of this architecture when they add concrete implementation value:

| System | Implementation role |
|---|---|
| UOR Framework | Identity substrate and addressability model |
| EvolveAI | Memory metabolism prototype and lifecycle engine candidate |
| CodeGenome | Graph substrate for software reality and provenance |
| COREFORGE Vault / Neurospace | Runtime memory implementation candidate |
| FailSafe / Arbiter | Governance enforcement, evidence capture, and approval implementation candidates |

PAMA is intentionally absent from this external implementation table because it is native doctrine. A runtime PAMA implementation may live in any conforming codebase while preserving the authority boundary.

Durable decision continuity is defined internally through [`profiles/durable-decision-memory-profile.md`](profiles/durable-decision-memory-profile.md). A product should be named as its implementation only after providing specific implementation evidence against that profile.

## Conformance expectation

Any implementation claiming alignment with this doctrine should be able to demonstrate:

1. deterministic identity or stable reference resolution;
2. durable provenance for memory creation and mutation;
3. calibrated saturation or equivalent lifecycle scoring where used;
4. trap-class resistance against access-spam and confidently-wrong promotion;
5. explicit PAMA mutation authority or an equivalent conforming authority model;
6. separate M0-M5 target, lifecycle strength, operation, and A0-A5 authority semantics where PAMA applies;
7. dispute and correction pathways;
8. audit evidence for crystallization and other consequential mutations;
9. safe pruning and deletion behavior;
10. governed recall across scope, tenancy, sensitivity, and dispute state; and
11. runtime evidence for any claimed conformance level.
