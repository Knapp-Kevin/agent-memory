# Future Subsystem: Multi-Agent Shared Memory Protocol

**Status: future subsystem. Not a core component.** This note exists because the prerequisite guardrails now exist or are being explicitly matured: actor scope, consent, and tenancy ([`../29-actor-scope-consent-and-tenancy.md`](../29-actor-scope-consent-and-tenancy.md)), privacy and sensitivity ([`../19-privacy-and-sensitivity-classifier.md`](../19-privacy-and-sensitivity-classifier.md)), interoperability profiles ([`../35-interoperability-profiles.md`](../35-interoperability-profiles.md)), and the **Proposed** memory-isolation-domain contract ([`../41-memory-isolation-domains-and-governed-crossing.md`](../41-memory-isolation-domains-and-governed-crossing.md)). Promotion into the component architecture still requires its own ADR, protocol specification, and conformance surface.

The isolation-domain material below is reconciliation with **ADR-022 (Accepted)**, not promotion of this future subsystem.

## Concept

Shared memory across agents, teams, or organizations multiplies memory's value and its blast radius by the same factor. Every single-system failure mode in the threat model acquires a propagation vector: one poisoned memory becomes every subscriber's poisoned memory, one over-broad scope becomes an organization-wide leak, one agent's bad correction becomes everyone's regression.

## Isolation-domain reconciliation

A shared memory space is an explicit **governed memory isolation domain**. It is not a hole in the isolation model and it is not equivalent to a shared physical store.

```text
shared store != shared memory domain
membership != recall admission
membership != write authority
membership != export authority
membership != re-sharing authority
```

A deployment may host private, project, task, and shared domains in the same storage service. Storage co-location does not collapse those logical authority boundaries.

### Entering and leaving a shared space

When an operation changes the authorized memory boundary, it is a governed crossing. Examples include:

```text
private -> shared
project -> shared
shared -> private
shared -> another shared domain
agent A private -> agent B private
```

The concrete operation may be `share`, `export`, `import`, `copy`, `summarize_for`, `derive_for`, `inherit`, or another transfer. If the authority boundary broadens or changes, the consequential decision must be evaluated through the isolation-domain/PAMA boundary and remain reconstructable.

A serialization, API call, or copy operation is not itself authorization.

### Membership and recall

Membership in a shared domain establishes at most **eligibility for governed use**. The receiving or recalling context must still resolve current actor/principal, purpose, delegation, sensitivity, domain membership, and other applicable admission constraints.

A memory may therefore be:

```text
visible to a trusted shared-space retriever
  and
semantically relevant
  and
associated with the same agent
  yet
blocked from active context
```

The governed recall planner runs on the receiving side. Candidate generation and membership cannot override recall admission.

### Shared derivation

A summary, embedding, extracted entity, synthesized memory, or other representation created for a shared domain does not shed source restrictions merely because its content is transformed.

Absent an explicitly authorized scope-promotion decision, derived state follows the isolation-domain default:

```text
derived allowed audience <= intersection(source allowed audiences)
derived allowed purpose  <= intersection(source allowed purposes)
derived restrictions     >= union(source restrictions)
```

If the compatible intersection is empty, derivation or subsequent admission must fail closed, narrow, or enter an explicit governed scope-promotion path. Choosing the broadest source scope is not a valid reconciliation rule.

### Tenancy boundary

This future subsystem continues to assume shared spaces operate **within a tenancy boundary**. ADR-022's ability to represent external destination domains does not silently authorize this protocol to perform cross-tenant shared memory.

Any future cross-tenant shared-memory protocol would require its own explicit authority, privacy, interoperability, and conformance treatment.

## Ownership model

- Every shared memory has exactly one **owner principal** (doc 29), the authority for correction, scope change, and deletion. Sharing distributes *access*, never ownership.
- Shared spaces (team pools, organizational memory) are themselves owned: a space has an owning principal, a governed isolation-domain identity, membership state, scope record, and admission policy. "Commons" without an owner or boundary is how contamination becomes permanent.
- Ownership transfer is a governed mutation with receipts, not a side effect of copying.

## Agent identity and delegation

- Every participating agent has a resolvable identity and acts under a delegation chain terminating at an accountable principal, scoped, purpose-bound, time-bounded, and non-transitive by default, per doc 29.
- An agent's writes into shared memory carry its identity and delegation ref; anonymous shared writes are unattributable sources and classed accordingly ([`../16-source-trust-and-reputation.md`](../16-source-trust-and-reputation.md)).
- Agent-to-agent assertion is a distinct source class: agent B's claim received by agent A is evidence *that B asserted it*, never direct evidence of the claim. Trust composes across the chain, and it attenuates; it does not launder.
- Agent identity does not collapse domains. The same agent may be a member of several project, task, private, and shared domains while each retains independent admission and crossing authority.

## Tenant and role-based recall

- Cross-tenant boundaries remain absolute for this future subsystem per doc 29: shared spaces exist *within* a tenancy scope, and the cross-tenant relevance trap ([`../../fixtures/cross-tenant-relevance-trap.json`](../../fixtures/cross-tenant-relevance-trap.json)) applies with shared-pool stakes.
- Recall from a shared space evaluates the *recalling* agent's isolation domain, scope, role, purpose, membership, and delegation. Membership in a space is candidacy, not admission; the governed recall planner ([`../26-governed-recall-planner.md`](../26-governed-recall-planner.md)) runs on the receiving side.
- Sensitivity handling composes: a memory admissible to agent A working purpose P is not thereby admissible to A working purpose Q, and export from shared space to private context is a governed boundary crossing, not merely a copy.
- A task or project switch does not carry prior shared-memory admission authority forward. Active context must be re-evaluated against the target domain when the authority context changes.

## Shared writes and boundary crossing

Writing into a shared space is not automatically authorized by the ability to read from it.

Where the write changes domain availability or influence, the decision should bind at least:

- source and destination domain references
- actor and accountable principal
- purpose
- source memory or derivation references
- representation form
- sensitivity
- consent/delegation/membership evidence where applicable
- requested consequence and PAMA disposition
- policy/authority references
- expiry or revocation state where applicable
- outcome and timestamp

The repository's proposed machine-readable shape is [`../../schemas/boundary-crossing-receipt.schema.json`](../../schemas/boundary-crossing-receipt.schema.json). Executable reference evidence emits this shape, but that local evidence does not promote the future shared-memory protocol into core architecture.

## Shared correction and dispute

- Corrections route to the owner principal; consumers may dispute. A dispute in shared memory propagates to all subscribers *as dispute state*, blocked from canonical use everywhere at once, which is the point.
- Divergent local corrections of a shared memory are a conflict class for [`../17-conflict-resolution-engine.md`](../17-conflict-resolution-engine.md): resolution is governed, receipted, and propagated; last-writer-wins across agents is the concurrent-mutation failure with more writers.
- The human contract ([`../38-human-correction-ux-contract.md`](../38-human-correction-ux-contract.md)) survives sharing: a user correcting memory about themselves reaches every space that memory was shared into, with propagation receipts.
- A downstream copy or derivation that is no longer authorized after correction, revocation, or scope reduction must not remain admitted merely because its original crossing receipt was valid. Crossing evidence records a historical decision; it is not permanent authority.

## Contamination and poisoning mitigations

- **Admission control**: writes into shared spaces pass source trust, sensitivity, membership, and destination-domain checks at the space boundary, not just the writer's local policy.
- **Provenance quarantine**: memory derived from one agent's uncertified inference stays marked through every hop; subscribers can quarantine by lineage. See [`../../fixtures/sleeper-memory-poisoning.json`](../../fixtures/sleeper-memory-poisoning.json).
- **Blast-radius accounting**: shared-space mutations carry higher effective risk class per the proportionality dimensions of `04-governance-and-pama.md` because scope and fan-out are inputs and sharing can maximize both.
- **Revocation propagation**: deletion, correction, certification revocation, membership revocation, and applicable scope reduction propagate to subscribers with receipts per [`../28-retention-deletion-and-tombstones.md`](../28-retention-deletion-and-tombstones.md). A shared space that cannot demonstrate required propagation cannot claim the corresponding evidence profile.
- **Composition control**: memories individually admissible from different shared/private domains may still form a prohibited aggregate. Domain provenance must survive through the composition-risk gate.

## Isolation evidence expected from a future protocol

A future protocol-level conformance surface should be able to exercise at least:

- member versus non-member shared-space recall
- same-agent cross-project and cross-task refusal
- allowed read with prohibited export or re-sharing
- unauthorized scope promotion
- derived summary attempting to widen audience or purpose
- incompatible multi-source derivation
- task/project switch with prior-context residue
- membership or delegation revocation affecting later recall
- correction and deletion propagation across subscribers
- individually admissible memories producing a prohibited composition

Critical isolation failures are hard governance failures. They are not averaged away by good recall quality or high semantic relevance elsewhere.

## Promotion criteria into core

The protocol becomes core only when: an ADR proposes it; the six conformance cases sketched in `14-expanded-scope-recommendations.md` exist as fixtures (plus poisoning-propagation, correction-propagation, and the isolation-domain cases required by the then-current architecture); the protocol is expressed as adapter contracts over [`../34-adapter-contracts.md`](../34-adapter-contracts.md); and two implementations demonstrate governed exchange under Profile 6 evidence.

ADR-022 acceptance does not by itself satisfy those separate promotion criteria. A mature isolation-domain boundary is a prerequisite for shared memory, not proof that the future shared-memory subsystem is ready for core status.
