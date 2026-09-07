# Governed Memory Across Architecture Families

Status: **#67, #275, and #276 research complete.** This directory is not canonical doctrine.

## Purpose

Agent Memory is intended to govern retained state without assuming that memory must be represented as files, vectors, graphs, rows, events, latent state, or any single combination of them.

The completed #67 program asked a harder question than “which backend is best?”:

> **Which governance obligations remain invariant, and which implementation/evidence techniques change, when memory is represented and retrieved through fundamentally different architecture families?**

The original program became active after its sequencing prerequisites were completed:

- #46 runtime-evidence program
- #63 portable governance evidence / AgenTrust interoperability
- #68 memory isolation domains and governed boundary crossing

Its cross-architecture results are preserved here. New research must be bounded to a genuinely new implementation, capability, or abstraction question rather than reopening #67 as a permanent catch-all.

## Strategic scope intent

Agent Memory's early emphasis on governance, provenance, lifecycle, correction, forgetting, isolation, and authority was a **sequencing decision**, not a permanent product boundary.

Those surfaces were the best place to start because they establish the control plane needed before adding more powerful and less inspectable memory mechanisms. The long-term scope is broader: Agent Memory should be capable of encompassing explicit durable memory, lexical/vector retrieval, graph memory, event/log memory, consolidation and tiering, learned or latent predictive state, world-model memory, planning context, and hybrid compositions where evidence shows they improve the system.

The intended direction is therefore not:

```text
governance/provenance around somebody else's memory system
```

It is closer to:

```text
Agent Memory
  = governed memory substrate(s)
  + provenance / evidence
  + lifecycle / correction / forgetting
  + recall / context assembly
  + learned and explicit representations
  + predictive / world-state memory where justified
  + isolation / authority / PAMA
  + reconstructable runtime evidence
```

No current representation is protected by historical sequencing. If comparative evidence shows that a learned predictive representation, graph, retrieval architecture, or hybrid should become a first-class operational memory layer, the architecture should evolve accordingly while preserving only the governance invariants that survive pressure-testing.

## Research products

The original architecture-family foundation was tracked by #224 and closed out under #67.

- [`taxonomy.md`](taxonomy.md) — architecture-family vocabulary and boundaries
- [`analysis-contract.md`](analysis-contract.md) — common questions every family must answer
- [`governance-comparison-matrix.md`](governance-comparison-matrix.md) — bounded cross-family comparison with explicit evidence status
- [`hybrid-composition-patterns.md`](hybrid-composition-patterns.md) — governance of multi-stage memory compositions
- [`adversarial-scenarios.md`](adversarial-scenarios.md) — equivalent pressure tests for representative substrates
- [`opaque-latent-predictive-state.md`](opaque-latent-predictive-state.md) — #137 JEPA/latent predictive-state study and comparative architecture hypotheses
- [`closeout-synthesis.md`](closeout-synthesis.md) — finite #67 synthesis and the distinctions that survived the cross-architecture program

### Completed bounded follow-on research

The follow-on work did not reopen the completed taxonomy program.

- [`first-party-module-adversarial-comparison.md`](first-party-module-adversarial-comparison.md) — completed #275 comparison of EvolveAI and CodeGenome against materially relevant external peers
- [`first-party-module-adversarial-scenarios.json`](first-party-module-adversarial-scenarios.json) — matched negative-path scenarios from #275
- [`memory-native-logical-state-algebra.md`](memory-native-logical-state-algebra.md) — completed #276 pressure test of whether a new logical transition abstraction is needed
- [`memory-native-logical-state-algebra-closeout.md`](memory-native-logical-state-algebra-closeout.md) — #276 final `no_new_algebra` disposition and future falsification trigger
- [`logical-state-algebra-scenarios.json`](logical-state-algebra-scenarios.json) — cross-substrate scenarios and promotion gates used by #276

The #276 result is deliberately a non-invention result: existing lifecycle, currentness, isolation, PAMA, maintenance, evidence, and component contracts remained sufficient under the tested pressure. No ADR or stronger state engine is warranted without new implementation evidence.

## Evidence status

Every architecture claim must carry one of these evidence states:

```text
architectural_deduction
primary_research_supported
implementation_observed
benchmark_or_conformance_evidence
cross_architecture_reproduced
open_hypothesis
contradicted
not_yet_evaluated
```

A claim may carry supporting and challenging evidence simultaneously. Do not average them into a confidence score.

The source-neutral rule from the repository evidence-promotion policy remains controlling:

```text
origin / provenance
!= evidence strength
!= promotion authority
```

A paper, implementation, maintainer statement, benchmark, community report, local experiment, or architectural argument may all produce useful evidence. None becomes doctrine because of who or what produced it.

## Common architecture-neutral invariants under test

The original research pressure-tested these hypotheses repeatedly:

```text
retrieval relevance != recall permission
probabilistic discovery != durable write authority
canonical state != derived projection
correction != silent overwrite
historical evidence != current truth
successful deletion operation != forgetting proof
representation compression != scope erasure
predictive quality != action authority
external/runtime evidence != lifecycle satisfaction
```

The closeout synthesis records where those distinctions survived. Future work should attempt to falsify them when a new implementation creates a materially new counterexample rather than treating survival as guaranteed doctrine by repetition alone.

## Relationship to learned / predictive memory research

#137 tested the representation-agnostic hypothesis against opaque learned/JEPA-style predictive state. #230 and #246 extended that work into operational-memory and long-horizon planning comparisons.

Those completed research products are inputs to #274's learned/latent component lane. A new implementation should not create another generic “does predictive quality create authority?” research loop unless it exposes a genuinely new failure mode. Predictive quality remains evidence/influence, not action or mutation authority.

## Original #67 research sequence

```text
Phase A0  taxonomy + common analysis contract
Phase A1  architecture-family studies
Phase A2  hybrid-composition studies
Phase A3  select representative substrates
Phase A4  equivalent cross-architecture experiments
Phase A5  adversarial review and promotion decisions
```

That sequence is complete. #275 and #276 were finite follow-on questions generated by the closeout and #274 implementation program, and they are now complete as well.

## Promotion boundary

Research findings may move into numbered doctrine, ADRs, schemas, profiles, fixtures, or conformance only when the evidence-promotion policy is satisfied.

This directory preserves rejected hypotheses and doctrine-survives results instead of silently deleting them. The goal is a reconstructable research record, not a persuasive essay that remembers only successful arguments.
