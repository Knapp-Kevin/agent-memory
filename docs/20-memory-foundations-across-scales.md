# Memory Foundations Across Scales

## Purpose

This document broadens Agent Memory beyond software architecture into a disciplined theory of memory across biological, cognitive, social, evolutionary, and artificial systems.

The purpose is **not** to claim that an LLM agent is a brain, that a vector database is a hippocampus, or that biological mechanisms can be copied into software by renaming a few classes. Those analogies are seductive precisely because they are easy. The useful work is to identify recurring **functions, tradeoffs, and failure modes** while preserving the differences between substrates.

## Working definition

Memory is a system's capacity to let prior state alter future state through retained, reconstructable, or inherited information.

That definition is intentionally broader than storage.

A memory system must answer at least five questions:

1. **What changed because an event occurred?**
2. **What part of that change persists?**
3. **Under what conditions can it influence future behavior?**
4. **How can it be revised, suppressed, generalized, or forgotten?**
5. **What survives beyond the current process, session, individual, or generation?**

## Memory is a process, not a container

A useful cross-domain lifecycle is:

```text
experience / signal
      |
      v
encoding
      |
      v
working retention
      |
      v
consolidation
      |
      v
longer-term representation
      |
      +----> retrieval / reactivation
      |             |
      |             v
      |       reconsolidation / revision
      |
      +----> abstraction / generalization
      |
      +----> weakening / forgetting / deletion
      |
      +----> inheritance / transmission
```

Different systems implement these functions differently. The lifecycle is a comparison framework, not a claim of mechanistic equivalence.

## Five scales of memory

### 1. Biological memory

Biological memory includes multiple mechanisms operating at different scales:

- short-lived changes in neural activity
- synaptic plasticity
- distributed neural representations
- systems consolidation
- immune memory
- transcriptional and epigenetic memory
- genetically inherited information

These should not be collapsed into a single thing called "biological memory." A nervous system, immune system, cell lineage, and genome retain information using different mechanisms and over radically different timescales.

### 2. Cognitive memory

Cognitive memory describes functional distinctions in how organisms retain and use information.

Commonly useful categories include:

| Memory form | Functional role | Agentic analogy, with caution |
|---|---|---|
| Sensory memory | extremely brief persistence of incoming signal | raw observation buffer |
| Working memory | active, capacity-limited manipulation | current context / scratch state |
| Episodic memory | events situated in time and context | interaction or trajectory memory |
| Semantic memory | facts, concepts, generalized knowledge | durable knowledge graph / fact memory |
| Procedural memory | skills and learned procedures | policies, runbooks, reusable action patterns |
| Prospective memory | remembering intended future actions | commitments, scheduled intentions, pending obligations |
| Associative memory | learned relations among cues and outcomes | linked entities, embeddings, graph edges |
| Spatial memory | relationships among locations and environments | world models, environment maps, tool/UI topology |
| Affective/value memory | learned salience, reward, aversion | utility, risk, preference, reinforcement history |
| Social memory | identities, relationships, reputations | actor models, trust, permissions, interaction history |

These categories overlap. Human memory taxonomies are models of function, not perfectly isolated physical modules.

### 3. Agentic memory

Agentic memory is retained information that can influence an agent's future perception, reasoning, planning, tool use, action, or self-modification across a meaningful boundary such as a context window, session, task, process, or deployment.

Agentic memory therefore includes more than a retrieval store.

It may include:

- active context
- scratchpads and transient state
- conversation history
- episodic trajectory records
- semantic facts
- preferences and user models
- tool affordances and environment knowledge
- learned procedures and runbooks
- failures and corrections
- policy and governance state
- source reputation
- commitments and pending work
- summaries and abstractions
- model parameters or adapters when they are intentionally used as retained experience

### 4. Collective and institutional memory

Groups preserve information outside any one member.

Examples include:

- language
- stories
- norms
- documentation
- source control
- ledgers
- issue trackers
- procedures
- laws
- scientific literature
- organizational rituals

For multi-agent systems, this is directly relevant. Shared memory is not merely "one database multiple agents can query." It creates questions of ownership, authority, scope, conflict, versioning, consent, provenance, and succession.

### 5. Evolutionary and inherited memory

"Evolutionary memory" is useful only if defined carefully.

Evolution does not remember in the autobiographical sense. Rather, populations preserve information about historical selection pressures through inherited structure. At other biological levels, immune and epigenetic systems can also preserve information about prior exposures.

For this architecture, inherited memory means **information that influences a new agent or generation without requiring that agent to have directly experienced the originating event**.

Agentic examples include:

- pretrained model weights
- inherited policies
- seed knowledge
- organization-wide rules
- templates and schemas
- curated runbooks
- distilled failure patterns
- versioned world models
- inherited source reputation

This is a powerful category because it separates **experience memory** from **prior memory**.

## Timescale is a first-class dimension

The words short-term and long-term are too vague on their own.

Agent memory should describe the boundary it crosses.

| Timescale | Biological/cognitive intuition | Agentic interpretation |
|---|---|---|
| Immediate | milliseconds to seconds | token-local or step-local state |
| Working | seconds to minutes | active context and scratch state |
| Session | minutes to hours | current task or conversation state |
| Episodic | hours to days | retained interaction or trajectory |
| Long-term | days to months | durable facts, preferences, procedures |
| Remote | months to years | deeply consolidated, rarely changing knowledge |
| Intergenerational | beyond one organism/process | inherited policy, model, schema, institutional knowledge |

A better memory specification says **what persistence boundary matters** rather than merely calling something LTM.

## Memory content and memory control are different axes

A memory can be episodic or semantic while also being transient or durable.

A procedure can be highly trusted but rarely recalled.

A frequently recalled fact can be false.

A sensitive preference can be accurate but prohibited from broad retrieval.

Therefore memory architecture should keep at least these axes distinct:

```text
content type
persistence horizon
confidence
source trust
retrieval relevance
recall frequency
sensitivity
mutation authority
certification state
contradiction state
cost
scope / tenancy
```

Collapsing them into one "memory score" creates avoidable failure modes.

## Encoding is selective

No biological or practical artificial system can preserve every detail at equal fidelity forever.

Encoding therefore requires selection.

Agentic encoding questions include:

- Is this observation novel?
- Does it change an existing belief?
- Does it create a commitment?
- Is it evidence for a decision?
- Is it likely to matter later?
- Is it sensitive or prohibited?
- Is the source trustworthy?
- Is this raw evidence, interpretation, or synthesis?
- Can the same fact be reconstructed from an authoritative source instead of stored?

An architecture that stores everything has not eliminated selection. It has merely postponed it until retrieval, cost, privacy, contradiction, and context overload make the bill arrive later.

## Consolidation is transformation

Longer-term memory is often not a verbatim copy of experience.

Biological research on systems consolidation and memory transformation shows that memory representation can reorganize over time, with precise event detail and generalized gist following different trajectories.

Agentic systems should explicitly model similar *functional choices*:

- preserve raw event
- extract semantic facts
- synthesize a summary
- learn a procedure
- update a world model
- retain an exception
- generalize a pattern
- preserve provenance linking the abstraction back to evidence

The key requirement is that abstraction must not erase the evidence chain needed to audit or correct it.

## Retrieval is reconstruction under context

Recall is not the same as reading a byte-identical record.

An agent may retrieve:

- exact-address records
- semantically similar records
- graph neighbors
- temporally relevant events
- procedurally relevant experience
- policy-constrained memories
- synthesized summaries

The result is then interpreted in the current context.

This means recall quality depends on both **stored representation** and **retrieval policy**.

## Reconsolidation and correction

When a memory is retrieved and new evidence arrives, the system may need to update the retained representation.

For agents, this should be explicit rather than silently overwriting history.

Preferred pattern:

```text
retrieve old memory
      |
compare with new evidence
      |
classify: confirm | refine | supersede | contradict | split-scope
      |
apply authority policy
      |
preserve prior version + provenance
      |
write corrected or reconciled representation
```

This aligns with the repository's existing dispute and correction doctrine.

## Generalization is useful information loss

A system that retains every episodic detail but cannot extract reusable structure has memory without learning.

Generalization intentionally sacrifices detail to improve transfer.

Examples:

- many failed tool calls become one environment "gotcha"
- repeated user corrections become a stable preference
- many code incidents become one defensive rule
- repeated navigation trajectories become a runbook

Generalization should preserve exceptions when those exceptions materially change behavior.

## Forgetting is part of intelligence

Forgetting is not merely a defect.

It can:

- reduce interference
- remove stale beliefs
- preserve limited attention
- improve generalization
- reduce storage and retrieval cost
- limit privacy exposure
- enforce retention requirements
- reduce poisoning persistence
- prevent old policy from dominating new policy

A memory architecture with no forgetting policy eventually becomes a historical landfill with semantic search.

See `21-forgetting-consolidation-and-memory-metabolism.md`.

## Memory and identity

Memory contributes to continuity, but memory is not identity.

An agent may retain no session history yet keep a stable cryptographic identity. Another agent may inherit extensive memory while operating under a different principal or authority scope.

This preserves the repository's existing UOR doctrine:

```text
identity answers: what object or actor is this?
memory answers: what retained information can influence future state?
```

## Memory and truth

Memory is not truth either.

A memory can be:

- accurate
- inaccurate
- outdated
- disputed
- contextually scoped
- synthetic
- inferred
- maliciously planted
- valid historically but invalid now

Therefore:

```text
remembered != true
frequently recalled != true
highly relevant != true
high confidence != permanent
permanent != immutable
```

## Cross-scale design principles

The following principles survive the move from biological inspiration to agent engineering without requiring false equivalence:

1. **Capacity is bounded.** Selection matters.
2. **Memory has multiple timescales.** One store is rarely enough.
3. **Different memory functions deserve different representations.**
4. **Consolidation changes representation.**
5. **Retrieval changes future memory policy.**
6. **Interference is real.** More memory can produce worse behavior.
7. **Forgetting can be adaptive.**
8. **Generalization trades precision for transfer.**
9. **Context controls meaning.**
10. **Correction requires retained history and provenance.**
11. **Inherited knowledge is different from direct experience.**
12. **Memory changes behavior, so memory is a security and governance boundary.**

## Architectural implication

The canonical Agent Memory architecture should ultimately support three coordinated views:

### Functional view

```text
encode -> retain -> consolidate -> retrieve -> revise -> forget -> inherit
```

### Content view

```text
episodic | semantic | procedural | prospective | relational | policy | preference | correction | evidence
```

### Governance view

```text
identity | provenance | trust | relevance | authority | certification | sensitivity | scope | audit
```

No one view is sufficient on its own.

## Related documents

- `AGENTIC_MEMORY_SYSTEMS_CANONICAL_ARCHITECTURE.md`
- `01-layer-model.md`
- `02-lifecycle-state-machine.md`
- `03-scoring-and-decay.md`
- `20-memory-foundations-across-scales.md`
- `21-forgetting-consolidation-and-memory-metabolism.md`
- `22-agentic-memory-theory-and-development.md`
- `23-research-bibliography.md`
