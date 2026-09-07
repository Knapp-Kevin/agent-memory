# ADR-021: Portable Memory Governance Evidence Boundary

## Status

Proposed

## Context

Agent Memory now has a stronger boundary than a conventional memory framework.

It defines memory semantics, lifecycle, PAMA authority, governed recall, correction, deletion, provenance, derived-state obligations, and reconstructable decision receipts. The runtime-evidence program has also begun proving these contracts against a real memory substrate.

At the same time, adjacent governance ecosystems solve different parts of the trust problem:

- Microsoft Agent Governance Toolkit (AGT) provides runtime policy enforcement, identity, context accumulation controls, audit events, and memory-poisoning defenses.
- AgenTrust provides portable trust and attestation surfaces through projects including TRACE, Agent Manifest, cMCP, cA2A, conformance tests, and ecosystem integrations.
- Agent Manifest already binds memory baseline state and defines append-only checkpoint/delta evolution for key-value, vector, and graph memory representations.
- TRACE is evolving an independent `action_receipts` verification axis and already recognizes externally signed execution evidence as distinct from gateway-produced evidence.

These capabilities are complementary, but the boundary must be explicit.

A cryptographically valid memory mutation does not prove that the mutation was semantically authorized under Agent Memory doctrine. Likewise, proof that an authorized `DEL` operation occurred does not prove that derived summaries, embeddings, graph projections, caches, or other recoverable representations were actually removed.

The P4 canonical-and-derived-state design spike makes this distinction concrete:

```text
integrity of mutation
        !=
semantic authorization of mutation
        !=
lifecycle obligation satisfaction
```

A portable evidence ecosystem needs to verify the first two relationships without absorbing the semantics of the system that produced them.

The AgenTrust Fellowship discussion also creates a practical opportunity for a focused contribution: build a concrete technical artifact against a real ecosystem gap while preserving Agent Memory as an independent project and canonical doctrine source.

## Problem

Without an explicit interoperability boundary, several failure modes are likely.

1. **Doctrine leakage.** PAMA or Agent Memory lifecycle rules could be re-expressed inside TRACE, Agent Manifest, AGT, or another external system, creating competing definitions of the same authority semantics.
2. **Evidence inflation.** A verifier could treat a valid signature, checkpoint, or action receipt as proof of semantic correctness or deletion completeness when it only proves integrity or correlation.
3. **Authority inversion.** An attestation or runtime-policy system could accidentally become the source of permission for a memory-specific consequence.
4. **Privacy leakage.** Raw memories, full decision receipts, sensitive scope metadata, or reasoning context could be copied into portable evidence formats that were never intended to become memory stores.
5. **Coupling.** Agent Memory could become dependent on one attestation ecosystem, weakening its usefulness as a substrate-neutral reference architecture.
6. **Upstream overreach.** A useful integration could be attempted as a premature normative schema change in TRACE or Agent Manifest rather than first being demonstrated as a portable external evidence adapter.

## Decision candidate

Adopt a **portable memory governance evidence boundary**.

Agent Memory remains the canonical authority for:

- memory semantics
- PAMA
- memory-specific permitted and prohibited consequences
- lifecycle transitions
- recall admission
- correction and supersession
- deletion and forgetting semantics
- canonical versus derived state
- projection residue
- memory-specific conformance
- Agent Memory decision receipts

External governance and attestation systems MAY verify, correlate, transport, or attest to Agent Memory evidence without becoming authoritative for those semantics.

Short form:

> **Agent Memory decides what a memory consequence means and whether it is permissible. External trust systems may prove that the decision and execution occurred.**

## Rule 1: evidence does not create memory authority

No external receipt, signature, attestation report, checkpoint root, runtime policy verdict, or trust score creates Agent Memory permission by itself.

A valid external proof MAY establish facts such as:

- a particular runtime executed
- a particular policy hash was loaded
- a particular action was attempted or enforced
- a particular checkpoint descended from an earlier checkpoint
- a particular evidence issuer signed a receipt
- a particular receipt was bound to a particular execution

It MUST NOT be interpreted, without separate Agent Memory evidence, as proving:

- that a memory mutation was authorized by PAMA
- that a recall was safe to admit into context
- that a correction was semantically valid
- that deletion propagated through all derived state
- that forgetting obligations were satisfied
- that an estimator had authority to rebuild or mutate durable state

## Rule 2: Agent Memory keeps the canonical receipt

The full Agent Memory decision receipt remains an Agent Memory artifact.

Portable integrations SHOULD expose a minimal evidence projection rather than copying the entire internal receipt graph.

A portable projection should be sufficient to correlate and verify a decision without becoming a second memory store. Candidate fields include:

```text
evidence_type / version
issuer identity
issuer key reference
action_ref
memory action class
receipt_hash
policy / PAMA reference or hash
scope reference or non-sensitive scope digest
before-state reference
committed after-state reference
disposition
lifecycle-result reference when applicable
signature
```

The exact wire shape is not accepted doctrine yet. Implementation evidence should determine the minimum interoperable projection.

Raw memory content, hidden reasoning, full sensitive scope contents, and unnecessary personal data MUST NOT be included by default.

## Rule 3: verification layers remain separate

A verifier should be able to distinguish at least three layers:

### Layer A: evidence integrity and binding

Questions include:

- Is the evidence signature valid?
- Is the issuer trusted for this evidence type?
- Does `action_ref` bind the evidence to the intended runtime action?
- Does the receipt hash resolve to the expected Agent Memory receipt?
- Does the evidence correlate to the correct policy and state versions?

### Layer B: memory-governance disposition

Questions include:

- Did Agent Memory permit, deny, defer, or require review?
- Was the committed action inside the PAMA-permitted action set?
- Was the disposition produced under the expected policy and authority state?

This layer is asserted by Agent Memory evidence and may be independently checked by an Agent Memory verifier.

### Layer C: lifecycle obligation satisfaction

Questions include:

- Did deletion reach the transitive derivation closure?
- Did an independent residue sweep find undeclared recoverable state?
- Did correction supersede the expected projections?
- Was an estimator-mediated rebuild separately authorized?

Layer C MUST NOT be inferred from Layer A or Layer B.

A valid negative outcome is useful evidence. For example, a correctly signed receipt proving that deletion was authorized but residue remained is not a verifier failure. It is evidence of a failed lifecycle obligation.

## Rule 4: Agent Manifest checkpoint integrity and Agent Memory semantic governance are complementary

Agent Manifest may prove that memory evolved through a valid baseline or checkpoint/delta path.

Agent Memory may prove why that evolution was or was not permitted and whether its semantic obligations were satisfied.

For example:

```text
Agent Manifest:
  DEL(memory-123) is present in a valid append-only delta
  checkpoint N -> N+1 verifies

Agent Memory:
  deletion was authorized
  derived embedding E still survives
  lifecycle result = residual / incomplete
```

Both statements can be valid simultaneously.

Therefore:

> **A valid memory delta is not evidence of complete forgetting.**

An Agent Memory interoperability profile MAY correlate its receipt to an Agent Manifest memory checkpoint, but it MUST preserve the distinction between mutation integrity and lifecycle satisfaction.

## Rule 5: TRACE proves execution relationships, not Agent Memory semantics

TRACE or another portable attestation format may bind an Agent Memory evidence reference to a runtime execution.

The preferred initial pattern is external action evidence:

```text
TRACE / runtime action
        |
        v
portable Agent Memory governance evidence projection
        |
        v
canonical Agent Memory decision receipt
```

TRACE should not need to understand PAMA, projection residue, promotion semantics, or Agent Memory lifecycle classes in order to verify the binding.

Core TRACE schema changes are not required for the first implementation unless implementation evidence demonstrates a genuinely generic missing field and upstream maintainers choose to standardize it.

## Rule 6: use AgenTrust integrations before proposing core-spec ownership

The first AgenTrust-facing implementation SHOULD target the ecosystem integration surface rather than modifying a core AgenTrust specification.

Preferred sequence:

```text
Agent Memory reference evidence projection + verifier
        |
        v
end-to-end executable example
        |
        v
agentrust-io/integrations adapter
        |
        v
vendor-neutral conformance/test vectors
        |
        v
only then consider a TRACE / Agent Manifest spec proposal if evidence requires one
```

This keeps Agent Memory independent and gives upstream standards work an implementation basis rather than a speculative schema.

## Rule 7: AGT is an enforcement peer, not the semantic owner

AGT may later become an independent runtime-enforcement surface for Agent Memory decisions.

The safe composition is:

```text
P_memory = actions permitted by Agent Memory / PAMA
P_runtime = actions permitted by AGT or another runtime policy system

P_final = P_memory intersection P_runtime
```

A runtime governance layer MAY further restrict an Agent Memory-permitted action.

It MUST NOT widen the Agent Memory-permitted set for a memory-specific consequence.

AGT interoperability is not required for the first AgenTrust evidence wedge, but the portable receipt design should not make later AGT enforcement correlation difficult.

## Rule 8: the canonical home remains Agent Memory

PAMA, Agent Memory lifecycle doctrine, memory schemas, decision-receipt semantics, conformance definitions, and memory-specific governance rules remain canonical in:

`MythologIQ-Labs-LLC/agent-memory`

External integrations may link to or consume those contracts.

They must not become the canonical definition of those contracts merely because they attest to their execution.

The Agent Memory Apache-2.0 license permits reuse, but project stewardship and canonical doctrine location are separate from interoperability.

## First reference slice: P4.5 Portable Memory Governance Evidence

The first implementation should demonstrate the boundary against an actual memory lifecycle consequence rather than a synthetic `allow` example.

The recommended reference scenario is deletion completeness.

### Failure case

```text
1. canonical memory M exists
2. summary S, embedding E, and graph projection G derive from M
3. deletion of M is proposed
4. PAMA authorizes deletion
5. runtime executes the canonical delete
6. memory checkpoint records a valid DEL operation
7. portable Agent Memory evidence binds the governance decision to that action
8. independent Agent Memory residue sweep finds E still present

results:
  execution evidence         valid
  checkpoint evolution       valid
  governance authorization   valid
  deletion completeness      failed
```

### Success case

```text
M removed
S removed
E removed
G removed
independent residue sweep = zero undeclared residuals

results:
  execution evidence         valid
  checkpoint evolution       valid
  governance authorization   valid
  deletion completeness      satisfied
```

The contrast is the point of the wedge.

> **Proof that an authorized deletion operation occurred is not proof that the information was forgotten.**

## Required negative paths

The reference implementation should exercise at least:

1. valid receipt signature, wrong `action_ref`
2. valid action binding, unknown or untrusted evidence issuer
3. valid external evidence, missing canonical Agent Memory receipt
4. PAMA denial with a correctly evidenced negative outcome
5. runtime action executed despite Agent Memory denial
6. valid canonical delete with declared residual projection
7. valid canonical delete with undeclared residual projection
8. stale policy or state reference
9. scope mismatch between action and memory receipt
10. receipt replay against a different execution
11. estimator-mediated rebuild attempted without separate authorization
12. full success with zero undeclared residue

## Relationship to the runtime-evidence roadmap

This decision introduces a candidate **P4.5** slice between P4 derived-state proof and broader ecosystem benchmarking.

P4 remains the immediate semantic prerequisite because portable evidence should not standardize a lifecycle result the repository cannot yet compute and test.

P4.5 adds two things the current roadmap still needs:

- a second independent implementation/evidence surface beyond the first memory substrate
- a portable, cross-system evidence chain that does not collapse Agent Memory semantics into the external system

## Acceptance evidence required

This ADR MUST remain Proposed until at least the following are demonstrated:

1. a versioned external evidence projection exists
2. the projection does not require raw memory content
3. the canonical Agent Memory receipt remains independently resolvable and verifiable
4. valid and invalid evidence bindings are covered by test vectors
5. valid negative outcomes are represented without being mislabeled as verifier failures
6. a real deletion-completeness scenario distinguishes checkpoint integrity from lifecycle satisfaction
7. at least one Agent Manifest checkpoint correlation is demonstrated or explicitly ruled unnecessary with evidence
8. a TRACE/action-receipt-compatible integration is demonstrated without requiring TRACE to implement PAMA semantics
9. replay, wrong-action, wrong-scope, stale-policy, and unknown-issuer negative paths fail correctly
10. the implementation can operate without making Agent Memory dependent on AgenTrust
11. the first upstream contribution targets an integration/conformance surface before any core-spec change, unless AgenTrust maintainers explicitly request otherwise
12. the resulting boundary is documented clearly enough that a third-party verifier cannot reasonably mistake integrity proof for semantic lifecycle proof

Acceptance of this ADR does not require AgenTrust maintainers to adopt any Agent Memory-specific normative schema into TRACE or Agent Manifest.

## Consequences

### Positive

- gives Agent Memory a concrete public interoperability wedge
- preserves Agent Memory as an independent canonical project
- adds a second evidence ecosystem to the runtime-evidence program
- makes memory-governance results portable without exporting raw memory
- complements Agent Manifest memory checkpoints rather than competing with them
- gives TRACE-compatible verifiers a way to correlate memory governance with execution
- makes valid negative lifecycle outcomes verifiable
- provides a technically credible AgenTrust Fellowship contribution path
- creates a path toward future standards input based on working evidence

### Negative

- introduces receipt-correlation and trust-anchor complexity
- requires careful distinction among evidence issuer, runtime issuer, and memory authority
- creates another versioned compatibility surface
- may expose disagreements between Agent Memory and external governance systems that need explicit resolution rather than optimistic merging
- upstream integration acceptance is outside Agent Memory's control

## Rejected alternatives

### Move Agent Memory doctrine into AgenTrust

Rejected. AgenTrust solves portable trust and attestation problems; Agent Memory solves memory semantics and lifecycle governance. Moving PAMA or lifecycle doctrine upstream would blur responsibilities and make Agent Memory unnecessarily dependent on another ecosystem.

### Encode PAMA directly into TRACE

Rejected. TRACE should verify evidence and execution relationships without becoming a memory-governance specification.

### Treat Agent Manifest memory checkpoints as complete Agent Memory governance

Rejected. Checkpoint integrity proves controlled state evolution, not semantic authorization, recall safety, or transitive deletion completeness.

### Treat AGT as the owner of Agent Memory permission

Rejected. Generic runtime policy may narrow Agent Memory permission, but it must not create memory-specific authority that PAMA denied.

### Put raw memories or full Agent Memory receipts into portable evidence

Rejected by default because it creates privacy, retention, scope, and accidental-secondary-memory risks.

### Start with a core TRACE or Agent Manifest schema change

Rejected as the default sequence. A working adapter and conformance evidence should expose the generic need first.

### Build anomaly detection or agent quarantine as the initial wedge

Rejected for this slice. Agent Memory may emit high-quality signals such as poisoning suspicion, authority laundering, scope violation, policy drift, and projection residue. The decision to quarantine an agent belongs to a broader runtime-governance or detection system.

## Standardization trigger

A core upstream specification change should be proposed only if at least one implementation demonstrates that a generic interoperability requirement cannot be represented through existing external evidence, action-receipt, checkpoint, or integration mechanisms.

Candidate generic needs might eventually include:

- a standard governance-evidence reference
- a standard receipt-root reference
- a standard memory-checkpoint correlation field
- a standard distinction between action evidence and lifecycle-satisfaction evidence

These are hypotheses, not requirements.

## Related public context

- AgenTrust Fellowship discussion #23: https://github.com/orgs/agentrust-io/discussions/23
- TRACE verification depth and action receipts: https://github.com/agentrust-io/trace-spec/issues/66
- TRACE external execution evidence guidance: https://github.com/agentrust-io/trace-spec/issues/34
- AgenTrust integrations contribution surface: https://github.com/agentrust-io/integrations
- Agent Manifest memory checkpoint/delta implementation: https://github.com/agentrust-io/agent-manifest/blob/main/python/src/agent_manifest/_memory_delta.py
- Agent Manifest memory baseline/checkpoint specification: https://github.com/agentrust-io/agent-manifest/blob/main/spec/agent-manifest-spec-v0.2.md
- Microsoft Agent Governance Toolkit: https://github.com/microsoft/agent-governance-toolkit

These sources establish neighboring implementation and evidence surfaces. They do not define Agent Memory doctrine.

## Open questions

- What is the smallest portable projection that preserves verification without leaking sensitive memory metadata?
- Should the portable evidence issuer be the Agent Memory runtime, a dedicated evidence signer, or a deployment-specific authority?
- How should trust anchors for Agent Memory evidence be discovered without coupling to a single PKI?
- Should lifecycle-satisfaction results have their own signed artifact or remain a referenced Agent Memory conformance result?
- How should long-lived memory receipts rotate keys without breaking reconstructability?
- What correlation is needed between Agent Memory receipts and Agent Manifest memory checkpoint roots?
- Can one action legitimately reference multiple memory-governance receipts, and how should aggregation be verified?
- How should shared-memory or multi-agent authority appear without exposing tenant or principal details?
- Which parts of this model are generic enough to propose upstream after implementation evidence exists?

## Doctrine candidate

Memory governance and trust evidence are different responsibilities.

Agent Memory should remain authoritative for the meaning and lifecycle of retained state while allowing independent systems to prove, correlate, and attest to the consequences it governs.
