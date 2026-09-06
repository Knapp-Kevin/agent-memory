<p align="center">
  <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/brand/agent-memory-wiki-cover.png" alt="Agent Memory Wiki cover showing the MythologIQ Labs lineage and the Agent Memory layered memory emblem with a cyan inference spark." width="100%">
</p>

# Agent Memory

**A reference architecture for governed memory in autonomous and agentic systems.**

Agent Memory is about retained state that can influence future behavior without quietly acquiring truth, scope, permanence, or authority it has not earned.

It separates uncertain interpretation from governed consequence, preserves why state changed, and treats correction, isolation, temporal integrity, forgetting, and structural adaptation as first-class architectural responsibilities rather than cleanup work.

> **Agentic memory is retained state that can alter an agent's future interpretation, reasoning, planning, tool use, action, or adaptation across a meaningful persistence boundary.**

## The architecture in one view

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/agent-memory-flow.png">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/agent-memory-flow-light.png">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/agent-memory-flow-light.png" alt="Agent Memory governed memory loop showing interpretation, scope and isolation-domain resolution, PAMA authority outcomes, permitted consequences, retained state, governed recall admission, ranking and composition, and active agent context" width="100%">
  </picture>
</p>

The loop is intentionally split into responsibilities that many memory systems blur together:

1. **Interpret.** Experience becomes evidence, provenance, uncertainty, and a proposal.
2. **Govern.** PAMA resolves what consequences are permitted under current policy, scope, authority, and state.
3. **Commit.** A permitted consequence becomes explicit retained state with reconstructable evidence.
4. **Recall.** Retrieval creates candidates; governance decides what may enter active context.
5. **Revise or forget.** Correction, supersession, staleness, deletion, and residual derived state remain distinct and auditable.
6. **Adapt structure safely.** New memory shape may be discovered dynamically, but canonical structural mutation requires deterministic authorized policy or explicit human authority.

The governing ideas are compact:

> **Probabilistic epistemics. Governed consequences.**  
> **Uncertainty may propose. Authority constrains.**  
> **Memory shape may adapt. Structural authority may not be probabilistic.**

## Start with what you need

- **New to Agent Memory?** Start with **[Getting Started](Getting-Started)**, then **[Core Concepts](Core-Concepts)** for the vocabulary and invariants the architecture preserves.
- **Want the architecture in pictures?** Open **[Decision Flows and Memory Lifecycle](Decision-Flows-and-Memory-Lifecycle)** for lifecycle, PAMA, recall, correction, deletion, isolation, and evidence flows.
- **Designing a configurable or adaptive memory stack?** Read **[Mutable Memory Fabric](Mutable-Memory-Fabric)** for the Agent Runtime / Agent Memory / Agent Governance boundary, memory modules, routing, and structural-mutation safeguards.
- **Working with temporal memory or temporal policy?** Start with **[Temporal Memory Architecture](Temporal-Memory-Architecture)**, then use **[Cryptographic Temporal Commitments](Cryptographic-Temporal-Commitments)** and **[Temporal Policy and Governed Memory](Temporal-Policy-and-Governed-Memory)** for the detailed evidence and consumer views.
- **Implementing a memory system?** Use the **[Implementation Guide](Implementation-Guide)**, then move into **[PAMA](PAMA)**, **[Lifecycle and Forgetting](Lifecycle-and-Forgetting)**, **[Canonical and Derived State](Canonical-and-Derived-State)**, and **[Mutable Memory Fabric](Mutable-Memory-Fabric)** as needed.
- **Integrating with governance or approval systems?** Read **[Governance Projection](Governance-Projection)** for the vendor-neutral memory-to-governance boundary and consumer-adapter ownership model.
- **Reviewing security or isolation?** Start with **[Security and Privacy](Security-and-Privacy)** for scope, tenancy, isolation domains, sensitivity, leakage, and deletion boundaries.
- **Checking what is actually proven?** Read **[Conformance and Evidence](Conformance-and-Evidence)** first, then **[Runtime Evidence](Runtime-Evidence)** for what has actually executed.
- **Researching the foundations or influences?** Use **[Research and Sources](Research-and-Sources)** and **[Aligned Projects & Intellectual Lineage](Aligned-Projects-and-Intellectual-Lineage)**.

## Mutable memory fabric

Agent Memory is the memory system, not whichever persistence or retrieval technology happens to be configured today.

```text
Agent Runtime
    |
    v
Agent Memory
  semantics / lifecycle / provenance / scope
  PAMA / structural authority / routing / recall admission
    |
    +--> files / SQL / graphs / RAG / GraphRAG
    +--> vector / learned / JEPA-style representations
    +--> EvolveAI / CodeGenome candidate first-party modules
    +--> external memory-system adapters
    |
    v
Agent Governance peers
  DashClaw / AGT / other policy, approval, enforcement systems
```

Short-, medium-, and long-term memory are policy characteristics, not mandatory backend assignments. A deployment can choose different module combinations while the Agent Memory behavioral contract remains stable.

Structural adaptation is similarly separated from structural authority. Learned systems may discover and propose new domain or representation shape, but canonical structural consequences are committed only through deterministic versioned policy or explicit human authority, with review increasing as semantic impact, scope, migration cost, blast radius, and irreversibility grow.

See **[Mutable Memory Fabric](Mutable-Memory-Fabric)** for the complete boundary.

## Temporal memory architecture

Agent Memory treats historical identity, signer evidence, lifecycle currentness, consumer compatibility, and policy authority as separate layers rather than one ambiguous timestamped record.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/temporal-memory-architecture-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/temporal-memory-architecture.svg" alt="Agent Memory temporal architecture showing canonical memory, temporal commitment, optional UOR identity, signer and trust evidence, external temporal evidence, lifecycle currentness, governed projection compatibility, Dogwood temporal policy, Cedar and Cedarling consumers, and PAMA separation." width="82%">
  </picture>
</p>

The composition is intentionally modular:

```text
canonical memory
  -> temporal commitment and evidence
  -> lifecycle currentness
  -> governed compatible projection
  -> Dogwood / Cedar / Cedarling / other aligned consumer
  -> returned policy evidence
  -> PAMA
```

This gives aligned systems meaningful roles without asking any one of them to become the universal memory model. UOR can provide exact object identity. Dogwood can provide temporal-policy semantics. Cedar and Cedarling can provide authorization surfaces. Agent Memory preserves memory-specific provenance, lifecycle, scope, and authority boundaries across those interactions.

See **[Temporal Memory Architecture](Temporal-Memory-Architecture)** for the full visual and relationship model.

## Why retrieval alone is not enough

A retrieval system can answer **what looks relevant**. A governed memory architecture must also answer:

- Should this state have been retained at all?
- Is it still current, merely historically true, disputed, or superseded?
- Does it belong to this user, task, project, tenant, or shared domain?
- Is the source trustworthy in this scope?
- May the memory enter the current context?
- May an agent change durable or shared state because of it?
- Can the resulting consequence be reconstructed later?
- Can the memory be corrected without destroying history?
- Can a deletion request reach summaries, indexes, caches, graph edges, and other derived state?
- Can the memory system change its own structure without letting a model quietly become the schema authority?

That is the boundary Agent Memory is designed to make explicit.

## The separations that matter

The architecture resists convenient equivalences that become expensive failure modes later:

```text
identity       != truth
signature      != signer trust
historical truth != current truth
confidence     != authority
saturation     != truth
relevance      != permission
retrieval      != recall admission
proposal       != commit
same agent     != same memory scope
staleness      != falsity
supersession   != correction
delete action  != forgetting completeness
precedent      != standing permission
projection     != policy decision
module         != authority
structural proposal != structural commit
backend shape  != canonical memory semantics
```

These are not slogans pasted over a storage layer. They determine where evidence, policy, scope, lifecycle, structure, and authority must remain independently inspectable.

## Governance systems can consume memory without owning it

Agent Memory can expose remembered decision and temporal context to external policy, approval, and enforcement runtimes through governed projections:

```text
Agent Memory core
  -> governed projection
  -> consumer-specific adapter
  -> external governance runtime
```

The core keeps generally useful memory semantics. The projection carries vendor-neutral precedent, temporal context, material conditions, scope, validity, provenance, and outcomes. A consumer adapter owns product-specific policy vocabulary, risk interpretation, and verdict mapping.

The projection deliberately does **not** create a final permission. A prior approval is evidence about a prior case, not permanent authorization for a new one.

See **[Governance Projection](Governance-Projection)**, **[Temporal Policy and Governed Memory](Temporal-Policy-and-Governed-Memory)**, and **[Aligned Projects & Intellectual Lineage](Aligned-Projects-and-Intellectual-Lineage)** for current aligned-system boundaries.

## Four jobs that should not collapse into one score

**Epistemics** estimates uncertain properties such as relevance, trust, contradiction, sensitivity, utility, and staleness.

**Governance** determines which consequences are allowed under current authority, policy, scope, and state.

**Commit** applies an explicit state transition and emits evidence sufficient to reconstruct why it happened.

**Recall** admits retained state into active context only when relevance and authorization both permit it.

A model may be highly confident and still be wrong. A memory may be highly reinforced and still be unauthorized. A retrieval result may be highly relevant and still belong to another scope. Agent Memory keeps those possibilities representable instead of averaging them into reassurance.

## Current maturity

Agent Memory separates doctrine maturity from implementation evidence so that one cannot impersonate the other.

| Area | Current state |
|---|---|
| **Accepted doctrine** | ADR-001 through ADR-020, ADR-022, ADR-024, ADR-028, ADR-030, ADR-031, and ADR-032 are **Accepted**. |
| **Portable governance evidence** | ADR-021 remains **Proposed** and independently maturity-gated. |
| **Durable mutation / evidence candidates** | ADR-023 and ADR-025 through ADR-027 remain **Proposed** under their individual evidence gates. |
| **Implementation portability** | ADR-028 is **Accepted**, preserving a language-neutral core with optional implementation/interoperability profiles. |
| **Governance Context Projection** | ADR-029 remains **Proposed** and independently evidence-gated. |
| **Temporal policy compatibility** | ADR-030 is **Accepted**. |
| **Temporal commitments** | ADR-031 is **Accepted**. |
| **Governed structural mutability** | ADR-032 is **Accepted**; current PAMA 1.2 remains conservatively review-first for `domain_schema_mutation` until narrower autonomous evidence is implemented. |
| **External temporal trust evidence** | Signer-trust binding, transparency evidence, and the exact OpenSSL RFC 3161 comparator are merged and repository-validated at their declared boundaries. |
| **Runtime evidence** | Executable reference paths cover governed mutation, deletion completeness, concurrency, temporal commitments, policy comparators, adversarial behavior, and systems characterization. |
| **Reference implementation** | A narrow evidence vehicle, not a claim of universal production readiness or higher cumulative conformance. |
| **Conformance claims** | Governed separately from individual evidence slices. Passing a runtime experiment does not automatically raise a cumulative conformance level. |

See **[Architecture Decisions](Architecture-Decisions)** for doctrine status and **[Runtime Evidence](Runtime-Evidence)** for the executable evidence ledger.

## Explore the architecture

- **[PAMA](PAMA)** for proportional mutation authority and consequence governance
- **[Lifecycle and Forgetting](Lifecycle-and-Forgetting)** for strengthening, correction, dispute, pruning, and forgetting
- **[Canonical and Derived State](Canonical-and-Derived-State)** for staleness, deletion propagation, residue, and rebuild authority
- **[Governed Uncertainty](Governed-Uncertainty)** for deterministic boundaries around probabilistic discovery
- **[Mutable Memory Fabric](Mutable-Memory-Fabric)** for configurable memory modules, routing, structural mutability, and the Agent Runtime / Agent Memory / Agent Governance boundary
- **[Governance Projection](Governance-Projection)** for vendor-neutral remembered context supplied to external governance consumers
- **[Temporal Memory Architecture](Temporal-Memory-Architecture)** for the full temporal evidence and aligned-consumer stack
- **[Cryptographic Temporal Commitments](Cryptographic-Temporal-Commitments)** for exact temporal identity and evidence
- **[Temporal Policy and Governed Memory](Temporal-Policy-and-Governed-Memory)** for Dogwood, Cedar, Cedarling, and consumer compatibility
- **[Security and Privacy](Security-and-Privacy)** for isolation domains, scope, tenancy, sensitivity, and leakage risks
- **[Decision Flows and Memory Lifecycle](Decision-Flows-and-Memory-Lifecycle)** for the complete visual architecture set
- **[Glossary](Glossary)** when two familiar words turn out to mean inconveniently different things

## Canonical source and contribution path

The Wiki is the reader-facing navigation and explanation layer. Canonical doctrine, schemas, fixtures, evidence, and ADR status live in the repository itself.

- **Canonical repository:** https://github.com/MythologIQ-Labs-LLC/agent-memory
- **Documentation index:** https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/README.md
- **Architecture decisions:** https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/docs/adr
- **Runtime evidence program:** https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/docs/programs/runtime-evidence
- **Contributing:** **[Contributing](Contributing)**

If a Wiki summary and a canonical repository source ever disagree, the canonical source wins. The useful response is to fix the Wiki, not to hold a committee meeting between two Markdown files.
