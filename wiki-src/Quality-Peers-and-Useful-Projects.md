# Quality Peers and Useful Projects

Agent Memory should make excellent independent work easier to discover.

This page highlights products, repositories, platforms, specifications, and technical systems that contribute real value to the agent, governance, trust, security, and memory ecosystem. Some directly influence Agent Memory. Some are interoperability targets. Some are comparators. Some simply do something well enough that practitioners should know they exist.

> **Good work should be visible. Credit should be generous. Boundaries should remain precise.**

The canonical recognition policy is [`docs/ecosystem/quality-peer-recognition.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/ecosystem/quality-peer-recognition.md). Intellectual-lineage and licensing details remain in **[Aligned Projects & Intellectual Lineage](Aligned-Projects-and-Intellectual-Lineage)**.

## What recognition means

```text
quality recognition
!= dependency
!= endorsement
!= sponsorship
!= formal partnership
!= conformance
!= architectural authority
```

A project can be excellent without Agent Memory adopting it. An interoperability target can be useful without either project controlling the other. A comparator can expose architectural value without becoming a normative dependency.

## Current highlights

| Project | Why it stands out | Current relationship |
|---|---|---|
| **UOR Foundation / UOR Framework** | Deterministic object reference, exact identity, replayable derivation concepts | quality peer / intellectual lineage / optional temporal identity profile |
| **DashClaw** | Serious treatment of pre-execution governance, approvals, enforcement posture, liveness, and evidence | enforcement peer / interoperability target / comparator |
| **Microsoft Agent Governance Toolkit** | Broad open governance surface around policy, identity, audit, and runtime controls | policy/enforcement peer / interoperability target |
| **AgentTrust / TRACE** | Cryptographically bound governance evidence, attestation, verification, and conformance surfaces | evidence/attestation peer / comparator |
| **Open Policy Agent** | Mature general-purpose policy engine with a strong deterministic external-decision surface | validated real policy comparator |
| **Cedar** | Purpose-built authorization model with principal/action/resource/context and permit/forbid semantics | validated real policy comparator |
| **Cedarling** | Embedded/local Cedar PDP with identity, policy-store, logging, OPA and AuthZen deployment surfaces | quality peer / policy-runtime interoperability candidate |
| **Dogwood** | Cedar-derived temporal policy over bounded event history, typed event schemas, providers, and explicit partition semantics | temporal-policy peer / interoperability target / exact-source comparator |

## Temporal interoperability cluster

The UOR, Dogwood, Cedar, and Cedarling relationships have materially matured beyond simple comparison.

```text
Agent Memory temporal commitment
  -> optional UOR exact identity
  -> lifecycle/currentness
  -> governed compatible projection
  -> Dogwood temporal policy or Cedar-family authorization
  -> returned decision evidence
  -> PAMA
```

This is not a product bundle. It is an architectural composition in which each system keeps its own responsibility.

See **[Temporal Memory Architecture](Temporal-Memory-Architecture)** for the full visual model.

---

## UOR Foundation / UOR Framework

UOR is particularly useful for thinking precisely about identity. Agent Memory's main architectural takeaway remains the distinction between exact object identity and the separate question of what that object is permitted to become or influence as memory.

**Repository:** https://github.com/UOR-Foundation/UOR-Framework

ADR-031 now gives that distinction an executable temporal role. Agent Memory can use the existing UOR-Addr compatibility profile to produce an exact portable reference to a canonical temporal commitment.

```text
TemporalCommitment
  -> exact content
  -> optional UOR-Addr reference
```

The boundary remains explicit:

```text
UOR identity != truth
UOR identity != signer trust
UOR identity != currentness
UOR identity != authority
```

Current UOR `DerivationTrace` concepts are also useful comparison material for ordered replayable derivation. Agent Memory does not infer a signing, clock, trust, or policy authority from those concepts.

See **[Cryptographic Temporal Commitments](Cryptographic-Temporal-Commitments)** and **[Aligned Projects & Intellectual Lineage](Aligned-Projects-and-Intellectual-Lineage)**.

---

## DashClaw

DashClaw is an independent governance runtime focused on the seam immediately before agent actions execute. Its emphasis on interception, risk/policy decisions, approval, evidence, and enforcement liveness makes it a useful parallel system rather than a competing memory implementation.

**Repository:** https://github.com/ucsandman/DashClaw

The particularly useful architectural lesson is simple:

```text
policy decision
!= approval evidence
!= enforcement point reached
!= action outcome
```

Agent Memory should be able to provide governed context to systems like DashClaw without absorbing their product-specific vocabulary into canonical memory semantics.

---

## Microsoft Agent Governance Toolkit

Microsoft Agent Governance Toolkit is a substantial open-source governance system covering deterministic policy, identity verification, audit, and runtime controls.

**Repository:** https://github.com/microsoft/agent-governance-toolkit

Its strongest value here is as a peer for testing responsibility separation:

```text
memory-specific governance
!= general agent policy
!= runtime enforcement
```

Agent Memory remains the semantic owner of memory lifecycle and PAMA consequences. A broader governance runtime may further constrain execution but should never silently widen a memory consequence Agent Memory denied.

---

## AgentTrust / TRACE

TRACE provides an open specification and tooling ecosystem for cryptographically bound AI-agent governance evidence.

**Repository:** https://github.com/agentrust-io/trace-spec

Current public material describes TRACE v0.2 as a developer-preview specification with a conformance test suite. Trust Records bind facts such as runtime, policy, environment, data class, and tool usage into verifiable evidence.

That is valuable precisely because Agent Memory keeps a strict boundary:

```text
verified identity != memory authority
valid attestation != semantic correctness
runtime evidence != lifecycle satisfaction
```

Agent Memory already uses a pinned TRACE package as a bounded evidence comparator.

---

## Open Policy Agent

OPA is a mature general-purpose policy engine and a strong example of policy-as-code that does not need to become Agent Memory's policy model in order to be useful.

**Repository:** https://github.com/open-policy-agent/opa

Agent Memory has executed its generic monotonic external-policy contract against pinned OPA v1.19.0. The surviving rule is:

```text
Agent Memory allow + OPA deny -> deny
Agent Memory deny + OPA allow -> still deny
policy result -> not execution evidence
```

That makes OPA both a useful product in its own right and a validated architectural comparator.

---

## Cedar

Cedar is a purpose-built authorization language and engine centered on explicit principal, action, resource, context, permit, and forbid semantics.

**Repository:** https://github.com/cedar-policy/cedar

Agent Memory has executed the generic external-policy seam against Cedar v4.12.0, exact source commit `fdcbaed32bdb8c8d13e4eaf2b58db5555e9fb8c5`.

Cedar was especially valuable because its authorization result is structurally different from OPA. The adapter binds the result to the exact request and policy artifact rather than relying on arbitrary result metadata.

Accepted ADR-030 adds another boundary: a memory-derived projection must be semantically compatible and current for the exact Cedar policy/schema contract before it is treated as current policy input.

Cedar policy identity and determining policy IDs remain evidence; ALLOW/DENY remains a policy decision, not execution or enforcement evidence.

---

## Cedarling

Cedarling is maintained inside the Janssen Project and builds a practical local authorization layer around Cedar.

**Repository:** https://github.com/JanssenProject/jans/tree/main/jans-cedarling

Current stable research pin:

- Janssen / Cedarling `v2.3.0`
- exact release commit `f7c6e34be6ac8d585a9d7b6f7a12921b440b495b`
- Cedarling package version `2.3.0`
- embedded `cedar-policy = 4.11.2`

Agent Memory's direct Cedar comparator targets v4.12.0. Those are separate evidence lines and should remain visibly separate.

Cedarling adds useful deployment/runtime surfaces around Cedar, including policy-store identity/version, trusted issuers, JWT/multi-issuer and unsigned authorization paths, dynamic context data, decision/system/metric logging, multiple bindings, OPA integration, and AuthZen surfaces.

The temporal-memory relationship is increasingly concrete: Agent Memory can project current memory-derived context into a Cedarling decision surface while preserving source currentness and the identity of the context actually evaluated.

Cedarling context precedence makes that evidence important:

```text
inline request context
>
pushed context data
>
default context
```

The boundaries remain strict:

```text
validated JWT != Agent Memory authority
Cedarling ALLOW != approval
policy-store version != standing authority
decision log != enforcement witness
```

Cedarling is **not** an adopted Agent Memory dependency.

---

## Dogwood

Dogwood is a Cedar-derived governance language for AI agents and tools that adds bounded temporal conditions over an event history. Its public model supports temporal predicates, typed/custom event schemas, information providers, compilation/lowering into Cedar context, and pluggable policy/temporal backends.

**Repository:** https://github.com/dogwood-policy/dogwood

Current Agent Memory comparator pin:

- public source commit `c6237c88099b3f492ecc5fcee42df06a19224b97`
- Apache-2.0 public repository
- reference interpreter explicitly not presented as production enforcement
- no public GitHub release artifact at the current research snapshot

Dogwood matters because it exercises a policy question that the existing OPA/Cedar comparators do not:

```text
what may policy conclude from a bounded history of prior events?
```

The relationship has now matured into a concrete semantic-mediation architecture:

```text
Agent Memory canonical history/currentness
  -> exact temporal evidence where available
  -> versioned governed event/context projection
  -> compatibility/currentness gate
  -> Dogwood temporal policy
  -> policy-decision evidence
  -> Agent Memory evidence boundary
```

This lets Agent Memory provide richer historical meaning without asking Dogwood to ingest the entire memory model. Dogwood contributes temporal-policy semantics without becoming the canonical memory store.

The boundaries remain strict:

```text
Agent Memory canonical history != Dogwood temporal trace
historical event match != current authority
Dogwood ALLOW != human approval
Dogwood decision != enforcement or execution evidence
```

Dogwood's public pin/partition semantics, bounded temporal windows, and trace-shape behavior expose concrete interoperability failure modes. A partial/asymmetric pin must not be mistaken for a partition guarantee, an insufficient temporal horizon is a capability mismatch rather than proof that no prior event occurred, and event projection shape can affect temporal semantics.

Accepted ADR-030 and the merged policy-projection compatibility evidence keep this contract provider-neutral, so Dogwood does not become a core dependency or define Agent Memory's canonical history model.

See **[Temporal Policy and Governed Memory](Temporal-Policy-and-Governed-Memory)** and **[Temporal Memory Architecture](Temporal-Memory-Architecture)**.

---

## How projects earn a place here

A project should be highlighted only when current primary evidence supports a real reason:

1. it is unusually useful or technically strong for practitioners;
2. it materially shaped an Agent Memory distinction;
3. it has served as a real comparator or reference substrate;
4. it exposes a useful interoperability, policy, enforcement, evidence, identity, observability, framework, or security boundary;
5. it contributed a falsifiable challenge that improved the architecture.

This is intentionally not an exhaustive software directory. There are already enough lists on the internet whose primary qualification is that somebody remembered a URL.

Entries should evolve as projects evolve. Strong work can earn greater prominence. Stale or materially changed projects can be reclassified. Recognition follows evidence.

## Source rights and independence

The default pattern is link + attribution + independent synthesis. Agent Memory does not copy logos, screenshots, code, diagrams, schemas, or marketing assets merely to make recognition look official.

See **[Aligned Projects & Intellectual Lineage](Aligned-Projects-and-Intellectual-Lineage)** and the canonical [Source Rights and Reuse Policy](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/SOURCE_RIGHTS_POLICY.md).
