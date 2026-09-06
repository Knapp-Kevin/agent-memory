# Research Bibliography and Evidence Map

## Purpose

This bibliography anchors Agent Memory doctrine in relevant work from cognitive science, neuroscience, biological memory, and modern agent-memory research.

It is intentionally an **evidence map**, not a decorative pile of citations. Each source is listed because it informs a specific architectural question.

Last substantive research pass: **2026-08-10**.

## Evidence discipline

The repository uses biological and cognitive research as inspiration for **functions and tradeoffs**, not as proof that software agents share neural mechanisms.

Use these labels when importing ideas:

```text
MECHANISM
A process demonstrated in the source substrate.
Do not claim it exists in agents unless implemented and tested.

FUNCTIONAL ANALOGY
A similar problem or role appears in another substrate.
Useful for design hypotheses, not equivalence claims.

ENGINEERING PRESCRIPTION
A software requirement justified by agent-system evidence, governance, or operational risk.

OPEN HYPOTHESIS
Promising but not yet validated strongly enough to become doctrine.
```

---

# Cognitive and neural memory systems

## Working memory

### Baddeley, A. (2000). The episodic buffer: a new component of working memory?

- Source: [PubMed](https://pubmed.ncbi.nlm.nih.gov/11058819/)
- DOI: `10.1016/S1364-6613(00)01538-2`
- Relevance:
  - working memory is capacity-limited and actively integrated
  - transient active state differs from long-term retention
  - multimodal binding is a distinct function
- Agentic implication:
  - current context should be treated as active working state, not durable memory
  - context assembly is itself a memory function

## Episodic and semantic memory

### Manns, J. R., Hopkins, R. O., & Squire, L. R. (2003). Semantic memory and the human hippocampus

- Source: [PubMed](https://pubmed.ncbi.nlm.nih.gov/12691670/)
- DOI: `10.1016/S0896-6273(03)00146-6`
- Relevance:
  - distinguishes event memory from factual knowledge while showing shared acquisition dependencies
  - supports treating episodic and semantic memory as functionally distinct but interacting
- Agentic implication:
  - interaction records and generalized facts should not be represented as the same memory type

### Squire, L. R., & Zola, S. M. (1998). Episodic memory, semantic memory, and amnesia

- Source: [PubMed](https://pubmed.ncbi.nlm.nih.gov/9662135/)
- DOI: `10.1002/(SICI)1098-1063(1998)8:3<205::AID-HIPO3>3.0.CO;2-I`
- Relevance:
  - useful background on the episodic/semantic distinction and debates around neural organization
- Agentic implication:
  - taxonomies are functional models, not proof of isolated physical modules

## Procedural memory

### Cavaco, S. et al. (2004). The scope of preserved procedural memory in amnesia

- Source: [PubMed](https://pubmed.ncbi.nlm.nih.gov/15215216/)
- DOI: `10.1093/brain/awh208`
- Relevance:
  - demonstrates preserved acquisition and retention of complex skills despite severe declarative-memory impairment
- Agentic implication:
  - knowing **how** to perform a task is materially different from remembering facts about the task
  - procedural memory deserves first-class representation

### Willingham, D. B., Nissen, M. J., & Bullemer, P. (1989). On the development of procedural knowledge

- Source: [PubMed](https://pubmed.ncbi.nlm.nih.gov/2530305/)
- DOI: `10.1037/0278-7393.15.6.1047`
- Relevance:
  - procedural learning can develop without corresponding explicit declarative knowledge
- Agentic implication:
  - successful trajectories can justify procedure learning without turning every execution detail into semantic fact

## Prospective memory

### McDaniel, M. A. et al. (1999). Prospective memory: a neuropsychological study

- Source: [PubMed](https://pubmed.ncbi.nlm.nih.gov/10067781/)
- DOI: `10.1037/0894-4105.13.1.103`
- Relevance:
  - prospective memory concerns remembering to perform intended actions later
- Agentic implication:
  - commitments, pending obligations, future triggers, and follow-ups are memory objects, not merely scheduler configuration

---

# Consolidation, transformation, and remote memory

## Schema-assisted consolidation

### Tse, D. et al. (2007). Schemas and memory consolidation

- Source: [PubMed](https://pubmed.ncbi.nlm.nih.gov/17412951/)
- DOI: `10.1126/science.1135935`
- Relevance:
  - demonstrates rapid incorporation of new information into an established schema
- Agentic implication:
  - preexisting structured knowledge can change consolidation speed and representation
  - consolidation policy should consider compatibility with existing world models

## Systems consolidation and memory representation

### Kitamura, T. et al. / broader systems-consolidation literature

For current architectural grounding, see:

- [Neurobiology of systems memory consolidation](https://pubmed.ncbi.nlm.nih.gov/32027423/)
- [Memory consolidation](https://pubmed.ncbi.nlm.nih.gov/26238360/)

Relevance:

- memory can reorganize over time across distributed systems
- consolidation is not well described as copying a record from a short-term store to a long-term store

Agentic implication:

- a durable representation may be transformed, summarized, linked, or generalized
- provenance should connect transformed memory back to its evidence

## Recent evidence for representation reorganization

### Ko, S. Y. et al. (2025). Systems consolidation reorganizes hippocampal engram circuitry

- Source: [PubMed](https://pubmed.ncbi.nlm.nih.gov/40369077/)
- DOI: `10.1038/s41586-025-08993-1`
- Relevance:
  - reports time-dependent reorganization associated with shifts from event precision toward generalized responding
- Agentic implication:
  - useful long-term memory may intentionally trade episodic precision for generalizable structure
  - high-fidelity evidence should remain separately auditable when needed

### Lei, B. et al. (2025). Reconstructing a new hippocampal engram for systems reconsolidation and remote memory updating

- Source: [PubMed](https://pubmed.ncbi.nlm.nih.gov/39689709/)
- DOI: `10.1016/j.neuron.2024.11.010`
- Relevance:
  - current evidence that remote-memory recall can participate in subsequent memory updating
- Agentic implication:
  - retrieval and revision should be modeled as connected lifecycle events rather than unrelated database operations

---

# Forgetting and interference

## Retrieval-induced forgetting

### Anderson, M. C., Bjork, R. A., & Bjork, E. L. (1994). Remembering can cause forgetting: retrieval dynamics in long-term memory

- Source: [PubMed](https://pubmed.ncbi.nlm.nih.gov/7931095/)
- Relevance:
  - selective retrieval can impair later recall of competing information
- Agentic implication:
  - recall policy changes the effective memory environment
  - repeatedly surfacing one memory can suppress alternatives operationally even if they remain stored

### Wimber, M. et al. (2015). Retrieval induces adaptive forgetting of competing memories via cortical pattern suppression

- Source: [PubMed](https://pubmed.ncbi.nlm.nih.gov/25774450/)
- Relevance:
  - provides evidence for active suppression of competing memories during selective retrieval
  - frames the effect as adaptive interference reduction
- Agentic implication:
  - more retrieved context is not always better
  - systems should measure interference and consider deliberate retrieval exclusion

### Hulbert, J. C., & Anderson, M. C. (2020). Does retrieving a memory insulate it against memory inhibition?

- Source: [PubMed](https://pubmed.ncbi.nlm.nih.gov/31957596/)
- DOI: `10.1080/09658211.2019.1710216`
- Relevance:
  - further investigates interactions between retrieval and later forgetting
- Agentic implication:
  - reinforcement and retrieval frequency should not be treated as simple monotonic durability signals

---

# Biological memory beyond the nervous system

## Transcriptional memory

### Kamada, R. et al. / interferon transcriptional-memory study (2018)

- Source: [PubMed](https://pubmed.ncbi.nlm.nih.gov/30201712/)
- Relevance:
  - prior stimulation created chromatin-associated changes that altered later transcriptional response and persisted through cell division
- Agentic implication:
  - useful example of inherited state affecting future response without autobiographical recall
  - supports a broad distinction between direct-experience memory and inherited state

## Immune memory

### Lau, C. M. et al. / epigenetic control of innate and adaptive immune memory (2018)

- Source: [PubMed](https://pubmed.ncbi.nlm.nih.gov/30082830/)
- Relevance:
  - demonstrates distinct epigenetic states associated with innate and adaptive lymphocyte memory
- Agentic implication:
  - "memory" can refer to durable response adaptation without explicit event replay

## Current trained-immunity synthesis

### Divangahi, M., & Kaufmann, E. (2026). Evolution and development of innate immune memory

- Source: [PubMed](https://pubmed.ncbi.nlm.nih.gov/42397938/)
- DOI: `10.1126/sciimmunol.aeb7976`
- Relevance:
  - current synthesis of trained immunity, epigenetic and metabolic reprogramming, life-stage effects, and evolutionary conservation
- Agentic implication:
  - useful caution against equating inherited or adaptive state with conscious recall

---

# Agent memory architectures

## Generative Agents

### Park, J. S. et al. (2023). Generative Agents: Interactive Simulacra of Human Behavior

- Source: [arXiv](https://arxiv.org/abs/2304.03442)
- Relevance:
  - experience stream
  - dynamic retrieval
  - reflection into higher-level memories
  - memory-informed planning
- Architectural lesson:
  - memory is useful when it influences action and higher-level synthesis, not merely when facts can be retrieved
- Doctrine caution:
  - reflection is an inference and should retain provenance and uncertainty

## MemGPT

### Packer, C. et al. (2023). MemGPT: Towards LLMs as Operating Systems

- Source: [arXiv](https://arxiv.org/abs/2310.08560)
- Relevance:
  - hierarchical memory tiers
  - virtual context management
  - explicit movement between limited active context and larger external memory
- Architectural lesson:
  - context-window management and durable memory are related but distinct functions

## A-MEM

### Xu, W. et al. (2025). A-MEM: Agentic Memory for LLM Agents

- Source: [arXiv](https://arxiv.org/abs/2502.12110)
- Relevance:
  - dynamic memory organization
  - structured notes
  - linking
  - memory evolution
- Architectural lesson:
  - memory graphs can evolve as new experience changes interpretation of older memory
- Doctrine caution:
  - evolution requires explicit mutation history, authority, and conflict handling in governed systems

## Mem0

### Chhikara, P. et al. (2025). Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory

- Source: [arXiv](https://arxiv.org/abs/2504.19413)
- Relevance:
  - extraction, consolidation, retrieval
  - graph-enhanced memory
  - latency and token-cost evaluation
- Architectural lesson:
  - memory quality is an accuracy/cost systems problem, not only an information-retrieval problem

## Unified learned memory management

### Yu, Y. et al. (2026). Agentic Memory: Learning Unified Long-Term and Short-Term Memory Management for Large Language Model Agents

- Source: [arXiv](https://arxiv.org/abs/2601.01885)
- Relevance:
  - exposes store, retrieve, update, summarize, and discard as agent actions
  - learns short-term and long-term memory management jointly
- Architectural lesson:
  - memory operations can become part of agent policy
- Doctrine caution:
  - learned control should remain bounded by governance, privacy, and mutation authority

## Trustworthy memory search

### Zhang, J. et al. (2026). Beyond Similarity: Trustworthy Memory Search for Personal AI Agents

- Source: [arXiv](https://arxiv.org/abs/2606.06054)
- Relevance:
  - identifies memory search as a trust boundary
  - reports threats including cross-domain leakage, sycophancy, tool-call drift, and memory-induced jailbreaks
  - proposes task-conditioned admission between memory retrieval and model context
- Architectural lesson:
  - read-path governance is as important as write-path governance

---

# Memory evaluation and benchmarks

## LongMemEval

### Wu, D. et al. (2024). LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory

- Source: [arXiv](https://arxiv.org/abs/2410.10813)
- Evaluates:
  - information extraction
  - multi-session reasoning
  - temporal reasoning
  - knowledge updates
  - abstention
- Doctrine use:
  - baseline for conversational long-term memory evaluation

## MemoryArena

### He, Z. et al. (2026). MemoryArena: Benchmarking Agent Memory in Interdependent Multi-Session Agentic Tasks

- Source: [arXiv](https://arxiv.org/abs/2602.16313)
- Relevance:
  - couples memory with future action across interdependent multi-session tasks
  - shows strong long-context/recall performance does not guarantee strong memory-guided agent behavior
- Doctrine use:
  - supports evaluating memory by downstream action quality, not recall alone

## LongMemEval-V2

### Wu, D. et al. (2026). LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced Colleagues

- Source: [arXiv](https://arxiv.org/abs/2605.12493)
- Evaluates:
  - static state recall
  - dynamic state tracking
  - workflow knowledge
  - environment gotchas
  - premise awareness
- Doctrine use:
  - directly supports procedural memory, failure memory, environment models, and long-horizon experience retention

## LoCoMo-Plus

### Li, Y. et al. (2026). Locomo-Plus: Beyond-Factual Cognitive Memory Evaluation Framework for LLM Agents

- Source: [arXiv](https://arxiv.org/abs/2602.10715)
- Relevance:
  - tests memory use when implicit constraints, goals, or values matter even when later queries do not repeat the original wording
- Doctrine use:
  - useful for evaluating whether memory captures behaviorally meaningful latent constraints rather than surface facts only

---

# Research questions for Agent Memory

The following questions should drive future literature review and experiments.

## Encoding

- How should novelty be distinguished from noise?
- Which information should remain evidence rather than become memory?
- Can learned write policies outperform heuristics without increasing poisoning risk?

## Consolidation

- When should episodes become semantic abstractions?
- How should exceptions survive compression?
- When should multiple trajectories become a procedural memory?

## Retrieval

- How should exact, graph, semantic, temporal, and procedural recall be combined?
- When should a relevant memory be deliberately excluded?
- How should retrieval expose uncertainty and contradiction?

## Forgetting

- Can learned forgetting improve agent action without increasing catastrophic memory loss?
- How should interference be measured?
- When is archival better than deletion?

## Governance

- Which memory transitions require human approval?
- How should consent and purpose limitations survive summarization?
- How should memory mutation authority work across multiple agents?

## Inheritance

- What should successor agents inherit?
- How should inherited memory be distinguished from direct observation?
- How should inherited mistakes be detected and corrected?

## Evaluation

- Which benchmarks measure action improvement rather than recall?
- How should false permanence be measured?
- How should deletion completeness be tested across summaries, graphs, caches, and learned representations?

---

# Maintenance rules

When adding research:

1. record the source and publication date
2. state which architectural question it informs
3. label biological-to-agent transfer as analogy unless directly tested in agents
4. distinguish empirical evidence from theory, review, or benchmark proposal
5. prefer primary papers for consequential claims
6. include negative or conflicting evidence when it changes doctrine
7. do not promote a fashionable memory mechanism into architecture merely because it has a memorable acronym

The objective is not citation count.

The objective is a doctrine whose claims can be traced to evidence, implementation experience, or an explicitly labeled hypothesis.
