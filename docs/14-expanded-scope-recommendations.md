# Expanded Scope Recommendations

## Purpose

This document records recommended expansion areas beyond the originally stated scope.

The goal is not to absorb every adjacent idea into Agent Memory. That would recreate the same conceptual sprawl this repo exists to prevent. The goal is to decide which adjacent ideas deserve first-class component treatment, which should remain integrations, and which should stay outside the architecture until they prove necessity.

Expansion proposals must also preserve the governed-uncertainty boundary. Components that classify, infer, rank, predict, or discover may remain probabilistic. Components that authorize durable consequence must expose explicit policy and authority semantics.

PAMA is already native core doctrine. Expansion work may refine its implementation contracts, but should not treat it as an external subsystem to be adopted.

## Recommendation summary

| Recommendation | Placement | Priority | Governed-uncertainty posture | Rationale |
|---|---|---|---|---|
| Source trust and reputation | Component candidate | High | probabilistic estimate; never authority by itself | Memory depends on evidence quality over time |
| Conflict resolution engine | Component candidate | High | probabilistic conflict interpretation + governed consequence | Disputes need explicit resolution semantics beyond simple flags |
| Temporal causality model | Component candidate | High | mixed deterministic timeline + probabilistic causality | Memory changes over time and needs causal explanation |
| Privacy and sensitivity classifier | Component candidate | High | probabilistic classification feeding strict policy | Memory systems must classify what can be stored, recalled, or shared |
| Memory economics and budget policy | Component candidate | Medium | utility/cost estimates feeding bounded retention policy | Agents need cost-aware retention and context assembly |
| Human correction UX contract | Product plus component | Medium | human input enters governed correction path | Durable memory needs user-facing correction pathways |
| Ontology and schema registry | Component candidate | Medium | deterministic versioning and compatibility rules | Shared memory objects need stable schemas and type evolution |
| Query planner and recall strategy | Component candidate | Medium | probabilistic planning inside recall policy | Retrieval needs policy-aware planning, not raw similarity |
| Multi-agent shared memory protocol | Future subsystem | Medium | probabilistic collaboration under explicit ownership/scope rules | Team and org memory require ownership and scope controls |
| Memory threat model | Conformance plus governance | High | adversarial tests across deterministic and probabilistic boundaries | Poisoning and unauthorized mutation require explicit treatment |
| Policy-as-memory | Doctrine concern | Medium | policy content may evolve, policy authority must remain explicit | Policies are durable memory but need stronger authority rules |
| Memory compiler | Future subsystem | Low | probabilistic extraction; governed admission required | Useful later for compiling heterogeneous artifacts into memory units |
| Interoperability profile | Future standard | Medium | deterministic contract semantics with implementation freedom | Needed if multiple implementations claim doctrine conformance |
| Domain-specific memory packs | Integration pattern | Low | implementation-specific | Should not enter core doctrine unless cross-domain behavior emerges |

## Add now

These should be added to the architecture soon because they are foundational and affect multiple components.

### 1. Source trust and reputation

Memory quality depends on source quality.

The current architecture captures evidence and provenance, but it does not yet fully define how source reliability changes over time.

Recommended component:

```text
Source Trust and Reputation Layer
```

Responsibilities:

- estimate source reliability
- weight evidence by source class
- track source-specific calibration and failure history
- decay or demote sources that produce contradictions
- distinguish authoritative, observed, inferred, synthetic, user-provided, and agent-generated sources
- prevent a noisy source from dominating saturation
- preserve uncertainty and applicability scope for trust estimates

Failure modes:

- high-volume low-quality source inflates memory
- stale source remains trusted
- agent-generated memory recursively cites itself
- single-source claims become durable without corroboration
- trust score silently becomes permission to crystallize
- one domain's trust estimate is reused outside its calibration scope

Governance rule:

```text
source trust -> evidence weighting
source trust != mutation authority
```

### 2. Conflict resolution engine

Dispute state is necessary but not sufficient.

The system needs a governed way to interpret and resolve conflicts between memories, sources, policies, and time windows.

Recommended component:

```text
Conflict Resolution Engine
```

Responsibilities:

- detect and classify conflict
- rank or compare conflicting evidence
- estimate whether conflict represents contradiction, supersession, scope mismatch, or uncertainty
- propose correction, split-scope, demotion, retention of both claims, or escalation
- preserve minority or historical claims when relevant
- prevent silent overwrite

Conflict types:

- factual contradiction
- temporal supersession
- scope mismatch
- policy conflict
- source reliability conflict
- user correction conflict
- implementation drift
- estimator disagreement

Control rule:

Conflict detection and evidence ranking may legitimately be probabilistic.

The **resolution consequence** must be governed.

```text
probabilistic conflict interpretation
  -> policy-defined options
  -> permitted action set
  -> correction / split scope / dispute / escalation / retain both
```

Do not force uncertain interpretation into deterministic classification merely to make the diagram tidier.

### 3. Temporal causality model

Memory systems need to know not only what changed, but why it changed.

Recommended component:

```text
Temporal Causality Layer
```

Responsibilities:

- represent exact event order where known
- distinguish observed chronology from inferred causality
- link decisions to causes and consequences
- distinguish stale from superseded
- support causal recall
- preserve timeline of correction and drift
- attach confidence and provenance to inferred causal relations

This is especially important for decision memory, codebase evolution, organizational memory, and agent self-improvement.

Control rule:

```text
observed order may be deterministic
causal attribution may be probabilistic
policy consequence must not treat inferred causality as certain fact without appropriate evidence
```

### 4. Privacy and sensitivity classifier

A governed memory system must know which memory can be stored, recalled, exported, summarized, shared, or deleted.

Recommended component:

```text
Privacy and Sensitivity Classifier
```

Responsibilities:

- classify memory sensitivity
- preserve classification uncertainty
- apply retention boundaries
- prevent unsafe context assembly
- enforce local-first and encrypted storage expectations
- distinguish personal, organizational, security, financial, health, credential, and public data
- expose confidence, model version, calibration scope, and unknown/abstain state

This component should influence PAMA, Vault, context assembly, and conformance fixtures.

Critical rule:

```text
classifier uncertain != non-sensitive
```

For broad sharing, export, or cross-tenant use, uncertainty should trigger stricter handling or review rather than optimistic coercion.

### 5. Memory threat model

The doctrine already contains trap classes, but it needs a broader threat model.

Recommended document:

```text
docs/15-memory-threat-model.md
```

Threat classes:

- memory poisoning
- access-spam reinforcement
- hallucination permanence
- recursive self-citation
- source spoofing
- provenance stripping
- unauthorized mutation
- stale policy retention
- cross-user leakage
- overbroad context assembly
- malicious correction
- poisoned code graph evidence
- unsafe multi-memory composition
- estimator manipulation
- calibration drift exploitation
- policy bypass through stochastic planners
- authority laundering across component boundaries

The threat model should test both individual components and composition seams.

## Add soon

These are valuable but should follow the foundational components.

### 6. Memory economics and budget policy

Agent memory has resource costs.

The architecture should model cost, context budget, storage budget, retrieval budget, latency budget, and cognitive budget.

Recommended placement:

```text
Context Assembly Surface + Saturation and Decay Engine + Governance
```

Utility estimates may be probabilistic.

Retention and deletion consequences remain governed.

```text
predicted low utility -> prune/archive/delete candidate
predicted low utility != permanent deletion authority
```

This should not become a standalone component yet unless cost policy becomes complex enough to need one.

### 7. Ontology and schema registry

The architecture now has schemas, but it does not yet define schema evolution.

Recommended component candidate:

```text
Memory Schema Registry
```

Responsibilities:

- maintain memory-unit types
- version schemas
- define compatibility rules
- support migrations
- prevent implementation-specific fields from corrupting doctrine-level objects
- define typed representations for uncertainty, policy outcome, action sets, and receipts

Schema compatibility is a deterministic substrate concern even when the data represented by the schema is probabilistic.

### 8. Query planner and recall strategy

Current memory systems often confuse retrieval with memory.

A query planner would decide how recall should work across identity lookup, graph traversal, evidence search, runtime context, and policy constraints.

Recommended component candidate:

```text
Governed Recall Planner
```

Responsibilities:

- choose recall path
- combine exact, graph, semantic, temporal, and policy-aware retrieval
- respect certification state
- avoid disputed canonical use
- obey tenant and sensitivity boundaries
- produce recall explanations
- expose stochastic selection mode when relevant

Control rule:

```text
planner may probabilistically discover candidates
policy defines admissible candidates and actions
```

### 9. Human correction UX contract

Correction is a doctrine concept, but products need a user-facing contract.

Recommended placement:

```text
Correction and Dispute Surface
```

The architecture should define what users must be able to see and change:

- why a memory exists
- why it was recalled
- what evidence supports it
- which parts are inferred
- how uncertain the system is where material
- whether it is certified
- how to dispute it
- how to correct it
- what authority the correction carries
- how correction affects future recall

## Watch closely

These are promising but should not enter the core architecture too soon.

### 10. Multi-agent shared memory protocol

Shared memory across agents, teams, or organizations is important, but risky.

It introduces ownership, identity, consent, tenant boundaries, ACLs, role-based recall, delegation, source reputation, conflicting authority models, and probabilistic consensus.

Recommendation:

Keep as a future subsystem until single-agent and product-local memory boundaries are stable.

Before admission to core, require conformance cases for:

- conflicting agent estimates
- delegated authority expiry
- cross-tenant high relevance
- shared-memory correction rights
- source laundering through another agent
- consensus that is high-confidence but unauthorized

### 11. Interoperability profile

If multiple systems claim Agent Memory conformance, the repo will need profiles.

Potential profiles:

- Level 1: identity and provenance
- Level 2: lifecycle and decay
- Level 3: calibrated saturation
- Level 4: PAMA authority
- Level 5: certification and crystallization
- Level 6: governed uncertainty
- Level 7: cross-system interoperability

Recommendation:

Wait until adapter contracts, typed handoffs, and implementation ownership maps exist.

### 12. Memory compiler

A memory compiler could convert docs, traces, issues, PRs, decisions, code graphs, and chat transcripts into memory units.

This is powerful but dangerous if added too early.

A compiler will almost certainly rely on probabilistic extraction, entity resolution, summarization, and classification. Therefore its output must enter the normal evidence, uncertainty, admission, and governance path.

Recommendation:

Do not add as a component yet. Track as a future subsystem after source trust, conflict resolution, sensitivity, and certification are stronger.

## Keep outside core for now

These may integrate later but should not define the doctrine.

### Domain-specific memory packs

Examples:

- software-engineering memory pack
- sales memory pack
- personal productivity memory pack
- mental health support memory pack
- compliance memory pack

Recommendation:

Treat these as integration profiles or products, not core doctrine.

### Agent personality memory

Agent personality continuity may use memory, but it should not drive memory doctrine.

Recommendation:

Keep personality memory as a runtime/product concern unless it intersects identity, consent, correction, provenance, or governance.

### Prompt-template libraries

Prompt templates may consume memory but should not define memory.

Recommendation:

Keep outside core.

## Highest-value next additions

The next architecture pass should add or complete:

1. `docs/15-memory-threat-model.md`
2. `docs/16-source-trust-and-reputation.md`
3. `docs/17-conflict-resolution-engine.md`
4. `docs/18-temporal-causality-layer.md`
5. `docs/19-privacy-and-sensitivity-classifier.md`

Each should explicitly identify:

```text
what may be probabilistic
what must be deterministic or formally bounded
what authority it does not own
what uncertainty metadata crosses its boundaries
what conformance cases can falsify its assumptions
```

## Strategic recommendation

Do not market this as an agent memory library.

Treat it as a reference architecture for governed agent memory systems.

That lets EvolveAI, CodeGenome, COREFORGE, UOR, FailSafe, and future implementation systems remain separate while aligning to a common doctrine.

PAMA remains native doctrine within Agent Memory rather than another external implementation name in that list.

The long-term wedge is not memory recall.

The wedge is governed memory state transition and admission across identity, evidence, uncertain inference, lifecycle, authority, certification, forgetting, and runtime use.
