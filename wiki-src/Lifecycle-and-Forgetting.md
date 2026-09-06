# Lifecycle and Forgetting

Memory should have a history. Agent Memory therefore treats persistence, consolidation, revision, and forgetting as explicit lifecycle behavior rather than invisible side effects of a storage engine.

## Seven memory functions

```text
ENCODE → RETAIN → CONSOLIDATE → RETRIEVE → REVISE → FORGET → INHERIT
```

Each function asks a different architectural question.

| Function | Question |
|---|---|
| Encode | What experience becomes a memory candidate? |
| Retain | What crosses a persistence boundary? |
| Consolidate | What can be generalized, summarized, proceduralized, or modeled? |
| Retrieve | What retained state is relevant now? |
| Revise | How do correction, contradiction, and supersession change memory? |
| Forget | What should decay, suppress, archive, redact, tombstone, or delete? |
| Inherit | What may pass to a successor agent, team, or generation? |

## Lifecycle state is explicit

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/lifecycle-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/lifecycle-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/lifecycle-flow-light.svg" alt="Agent Memory lifecycle state map showing strengthening, governed promotion, demotion, dispute, correction, reconciliation, pruning, and the separation between transition proposal and commit" width="100%">
  </picture>
</p>

The diagram is an explanatory map of the canonical lifecycle state machine, not an independent transition table. Not every memory traverses every state. A transition proposal does not mutate lifecycle state; only a permitted transition may commit after validation. `Crystallized` means durable under current evidence and policy, not eternal, and `Pruned` does not necessarily mean deleted.

A compact view:

```text
Transient → Observed → Linked → Reinforced
                    ↓
Candidate → Pending verification → Crystallized
                                  ↓
                          Operational reuse
                                  ↓
                          Stale / Disputed
                                  ↓
                    Corrected → Reconciled
                                  ↓
                       Archived / Pruned
                                  ↓
                             Tombstoned
```

Not every memory traverses every state. The requirement is that consequential transitions remain explicit, scoped, authorized, and auditable.

## Forgetting is not one operation

Agent Memory distinguishes:

- decay
- suppression
- interference management
- deprioritization
- pruning
- archival
- compression
- semanticization
- supersession
- redaction
- tombstoning
- cryptographic deletion
- full-pipeline purge
- specialized model unlearning

Those operations differ in reversibility, evidence requirements, downstream effects, and authority.

## Utility does not grant deletion authority

```text
predicted low utility → forgetting candidate
predicted low utility != irreversible deletion authority
```

A model can recommend deletion. It does not gain permission to destroy durable evidence merely because the recommendation is confident.

## Derived state matters

Deleting one canonical record may leave behind:

- summaries
- embeddings and indexes
- graph edges
- caches
- exported copies
- consolidated semantic memories
- derived procedures
- telemetry or audit material

A deletion guarantee is only as strong as the propagation boundary it actually controls.

Two of those items are governed memory in their own right — a consolidated semantic memory carries identity, lifecycle, and derivation links. The rest are **projections**: infrastructure with no identity, no lifecycle state, and nothing obliging them to record what they were built from. That asymmetry is the point. The residue risk concentrates in exactly the state the architecture currently cannot see, and a projection's most dangerous property is not that it is stale but that it is *unaccounted for*.

Derived state also fails in a way canonical state cannot — by being out of date. Distinguishing the two failure modes is what makes deletion propagation testable rather than merely required:

```text
stale     a source changed         content may be wrong
residual  a source was purged      content may be prohibited
```

Staleness may be repairable by recomputation. Residue is not: it is a governance problem, and only the deletion authority may resolve it. **[Canonical and Derived State](Canonical-and-Derived-State)** develops both, along with the case where correction and deletion give opposite instructions about the same superseded summary.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/deletion-propagation-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/deletion-propagation-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/deletion-propagation-flow-light.svg" alt="Deletion completeness diagram showing canonical memory, governed derived memory and projection state, correction staleness versus deletion residue, transitive purge, independent residue verification, and incomplete forgetting when undeclared residue survives" width="100%">
  </picture>
</p>

The deletion requirement is canonical: verification must address the requested forgetting outcome and known derived state rather than merely prove that one storage row disappeared. The diagram's three-tier projection vocabulary and its exact P4 residue mechanics are **executed design evidence, not adopted doctrine**. That maturity boundary matters. A persuasive picture cannot accept ADR-020 for us. The useful operational distinction is still clear: source change creates staleness; source purge can create residual content; and a delete operation is not equivalent to demonstrated forgetting completeness.

## Correction is not erasure

Agent Memory prefers preserved history over silent overwrite.

```text
stale != false
superseded != corrected
historically true != currently true
```

When evidence changes, the architecture should preserve what was known, what changed, why it changed, and which newer state supersedes the old one.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/temporal-correction-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/temporal-correction-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/temporal-correction-flow-light.svg" alt="Temporal change diagram distinguishing historically true state that is later superseded, wrong or incomplete state that is corrected, uncertain state that is disputed, and old but historically valid state that is stale for current-state recall" width="100%">
  </picture>
</p>

The visual is an explanatory projection of the temporal-causality doctrine, not a replacement policy. Supersession means the older record was valid and a newer state applies later. Correction means the older record was wrong or materially incomplete within its claimed scope or time. Dispute preserves unresolved uncertainty rather than choosing a winner, while staleness can reduce current-state usefulness without making a historically valid record false. Chronology may be deterministic when the system has exact events and timestamps; causal attribution remains uncertain unless independently established.

## Canonical sources

- Lifecycle state machine: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/02-lifecycle-state-machine.md
- Temporal causality: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/18-temporal-causality-layer.md
- Forgetting and consolidation: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/21-forgetting-consolidation-and-memory-metabolism.md
- Retention, deletion, tombstones: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/28-retention-deletion-and-tombstones.md
- Recovery and replay: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/31-recovery-rollback-and-replay.md

## Next

- **[Canonical and Derived State](Canonical-and-Derived-State)** for how deletion and correction propagate into derived state
- **[Security and Privacy](Security-and-Privacy)** for deletion residue and lifecycle attack surfaces
- **[Conformance and Evidence](Conformance-and-Evidence)** for proving lifecycle behavior
