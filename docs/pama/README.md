# Proportional Adaptive Mutation Authority (PAMA)

## Status

PAMA is **native Agent Memory doctrine**, not an external source system or borrowed dependency.

The Proportional Adaptive Mutation Authority architecture originated with **Kevin R. Knapp**. Agent Memory adopts PAMA as a core governance foundation and specializes it for durable memory, procedural learning, policy, correction, deletion, scope, and agent action boundaries.

External frameworks used to evaluate or align PAMA, such as OWASP, NIST, or regulatory guidance, are evidence and alignment references. They are not the source of PAMA and do not change its authorship provenance.

## Foundational thesis

> **Adaptation should be broadly available to authorized agents. Authority to make a mutation durable, influential, shared, or action-enabling should increase in proportion to the mutation's consequence.**

PAMA exists to avoid three failure modes at once:

1. **stagnation**, where agents cannot form durable improvement loops;
2. **casual self-editing**, where observations silently become assumptions, defaults, procedures, or authority; and
3. **over-governance**, where every low-risk observation requires human approval and meaningful review collapses into fatigue.

The governing review rule is:

> **Review should be applied at promotion and consequence boundaries, not at every observation boundary.**

## Four separations

PAMA starts with four distinctions that Agent Memory must preserve:

```text
adaptation != authority
memory != procedure
procedure != permission
permission != governance
```

An agent may observe, infer, propose, or learn without automatically receiving authority to apply a durable or consequential change.

A remembered fact or preference does not automatically become an executable workflow.

A validated procedure does not automatically authorize execution.

Permission to act does not authorize an agent to expand, weaken, or redefine governance itself.

## Mutation target classes

PAMA classifies **what is being changed** separately from the operation used to change it.

| Class | Target type | Examples | Default posture |
|---|---|---|---|
| **M0** | Execution-local context | current-session correlation, temporary intent interpretation, local retrieval hint | transient; expire automatically |
| **M1** | Low-risk personal preference | formatting, terminology, view, pacing | tentative, visible, reversible |
| **M2** | Operational association | project routing, recurring task association, workflow suggestion | evidence-backed; recommendation influence |
| **M3** | Reusable procedure or capability | validated checklist, repair sequence, reusable workflow | validation and promotion controls |
| **M4** | Shared fact or identity-bearing state | relationship, entitlement, commitment, permission-affecting fact | authoritative evidence and controlled review |
| **M5** | Governance, security, or autonomous-action authority | policy exemption, trust elevation, send/deploy/delete authority | explicit authorization; no self-approval |

These target classes are foundational PAMA taxonomy. Agent Memory's mutation operations such as `promotion`, `correction`, `pruning`, `scope expansion`, and `policy mutation` are a separate dimension.

## Lifecycle strength

PAMA also distinguishes the strength of retained adaptive state:

```text
Observed -> Tentative -> Reinforced -> Promoted -> Canonical
                   \-> Decaying -> Archived / Deprecated / Blocked
```

Strength is not authority. A highly reinforced item may still be barred from external action. A tentative item may be retained safely while being prevented from influencing consequential behavior.

## Downstream authority classes

Every retained mutation should declare the maximum authority it may influence.

| Class | Authority | Meaning |
|---|---|---|
| **A0** | Retrieval only | may appear in inspection or context recall |
| **A1** | Recommendation influence | may affect rankings, suggestions, routing, or planning |
| **A2** | Draft generation | may shape drafts for human review but cannot execute them |
| **A3** | Local workflow mutation | may update authorized internal state |
| **A4** | External action | may affect messages, deployments, purchases, deletions, bookings, or provider state |
| **A5** | Governance change | may alter privileges, policies, trust, enforcement, or future autonomous authority |

A mutation's lifecycle strength and downstream authority must be evaluated together.

> **Validation can justify trust in a capability. It does not automatically grant permission to use that capability autonomously.**

## Proportional handling lanes

PAMA concentrates friction where consequence increases:

| Lane | Typical use | Core control |
|---|---|---|
| **1. Transient automatic** | M0 context and narrow interpretations | no durable authority or external effect |
| **2. Tentative low-risk retention** | M1 and selected recommendation-only M2 | visible, removable, scoped |
| **3. Evidence-backed reinforcement** | meaningful but reversible M2 | evidence, correction, conflict checks |
| **4. Promotion and review** | M3, shared knowledge, meaningful workflow behavior | validation, versioning, authority ceiling, rollback |
| **5. Restricted authority** | M4/M5 effects involving external action or governance | explicit authorized review, no self-approval, fail closed when authority is ambiguous |

## Adaptive mutation contract

A serious implementation needs a structured mutation proposal carrying at least:

```text
proposal identity
proposing agent and charter version
target reference, domain, class, and scope
mutation operation
current and proposed lifecycle strength
downstream authority ceiling
reversibility
evidence and validation references
corrections and failure evidence
confidence and uncertainty where applicable
freshness requirements
sensitivity
recommended handling
policy decision reference
```

Missing fields must not be interpreted as low risk. Unknown consequence is not presumed safety.

## Security and governance invariants

The following remain true regardless of implementation technology:

1. No mutation becomes more authoritative merely because a trusted agent proposed it.
2. Missing classification data must not auto-classify a high-impact mutation as low risk.
3. A reusable capability does not implicitly grant external-action or governance authority.
4. An agent must not approve its own expansion of privilege, trust, exception, or autonomy.
5. Evidence-bearing claims must not rely on fabricated or placeholder provenance.
6. Promotion must not rely only on recurrence, retrieval success, or model confidence.
7. Security-relaxing mutations require stricter treatment than protective observations.
8. Learned state remains subject to correction, staleness, conflict, revocation, and failure evidence.
9. Context assembly must preserve whether memory is tentative, promoted, canonical, stale, corrected, or disputed.
10. Claims of safe self-improvement require downstream outcome and authority-compliance evidence.

## Agent Memory specialization

Agent Memory operationalizes PAMA across several documents rather than treating it as a separate external project:

- [`../04-governance-and-pama.md`](../04-governance-and-pama.md) defines the memory-specific authority boundary and evaluation contract.
- [`../33-pama-decision-table.md`](../33-pama-decision-table.md) specializes PAMA into operation/risk decision data.
- [`../34-adapter-contracts.md`](../34-adapter-contracts.md) defines the typed PAMA handoff boundary.
- [`../36-policy-as-memory.md`](../36-policy-as-memory.md) applies PAMA to high-authority policy memory.
- [`../38-human-correction-ux-contract.md`](../38-human-correction-ux-contract.md) exposes correction and consequential review to humans.
- [`../adr/ADR-004-pama-controls-mutation-authority.md`](../adr/ADR-004-pama-controls-mutation-authority.md) makes PAMA canonical architecture doctrine.
- [`../adr/ADR-020-probabilistic-discovery-deterministic-governance.md`](../adr/ADR-020-probabilistic-discovery-deterministic-governance.md) applies PAMA to probabilistic discovery and governed consequence.

## Provenance rule

PAMA should not appear in the external source-rights registry merely because it has conceptual provenance. It is contributor-originated native doctrine in this repository.

External sources that challenge, support, benchmark, regulate, or provide implementation analogies for PAMA retain their own source and rights records.

## Doctrine

PAMA is not a memory score.

PAMA is not a human-approval-everywhere system.

PAMA is the architecture that allows adaptation while scaling mutation authority with consequence.

**Learning may be broad. Consequence remains governed.**
