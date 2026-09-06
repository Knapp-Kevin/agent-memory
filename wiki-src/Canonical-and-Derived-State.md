# Canonical and Derived State

> **Status: design executed, not adopted.** The vocabulary and invariants below began as a design spike and are now implemented and exercised in continuous integration, including the parts a persuasive demonstration would skip. No Architecture Decision Record has adopted them, and executing a bar is not the same as accepting the decision it supports. See **[Runtime Evidence](Runtime-Evidence)** for what that distinction means here.

Deleting a memory is easy. Proving it is gone is the hard part, and almost every hard case involves state that was *derived* from the memory rather than the memory itself.

## The problem in one paragraph

A user asks for a record to be deleted. The record disappears. But a summary written from it still contains the content, an embedding built from it still encodes it, a search index still points at it, and a cached view still serves it. Each of those is a legitimate piece of engineering. Together they mean the deletion was a gesture. **[Lifecycle and Forgetting](Lifecycle-and-Forgetting)** already says deletion must propagate through derived state. This page is about what that sentence has to mean before anyone can test it.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/deletion-propagation-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/deletion-propagation-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/deletion-propagation-flow-light.svg" alt="Deletion completeness diagram showing canonical memory, governed derived memory and projection state, then separating correction staleness from deletion residue, transitive purge, independent residue sweep, and lifecycle success only when undeclared residue is zero" width="100%">
  </picture>
</p>

The canonical requirement is that deletion propagate through known derived state and that verification answer the requested forgetting outcome rather than merely report that one row disappeared. The three-tier projection vocabulary and the exact `stale`/`residual` relation shown here are **executed P4 design evidence, not adopted doctrine**. The diagram therefore explains the current tested design without raising ADR-020 status or turning implementation vocabulary into a new canonical contract. Its critical distinction remains: a changed source creates a correctness problem; a purged source can create prohibited residual content. A delete operation is not proof of forgetting completeness.

## Three tiers, not two

"Canonical memory versus derived projections" sounds like one boundary. There are two, and the difference decides where the risk lives.

| Tier | What it is | Governed today? |
|---|---|---|
| **Canonical memory units** | Authoritative state. Can only be wrong on its own terms. | Yes — identity, lifecycle, authority, provenance |
| **Derived memory units** | Summaries, semantic and procedural memory. First-class memory that happens to have sources. | Partly — they carry derivation links and lifecycle state |
| **Projections** | Indices, embeddings, caches, materialized views, community summaries. | **No** — not memory units, so no schema, identity, lifecycle, or authority applies |

The third tier is the uncomfortable one. An index entry is not a memory unit, so nothing obliges it to record what it was built from. A cache has no lifecycle state. An embedding has no authority governing its refresh. The two tiers already under observation are the two that were easiest to observe, and the residue risk is concentrated in the tier the schema cannot see.

## How to tell canonical from derived

Not by where it is stored, and not by whether the word "cache" appears in the variable name. The test is disagreement:

> If this state and its source disagree, which one is wrong?

Canonical state can only be wrong on its own terms. Derived state has a **second failure mode**: it can be wrong by being out of date. Every invariant below exists to make that second failure mode visible rather than silent.

## What a projection has to declare

For any of this to be checkable, projections need to declare their relationship to canonical state — not their contents, which are the storage engine's business.

| Field | Meaning |
|---|---|
| **Basis** | Which canonical units it was built from, and at which version of each |
| **Transform** | Deterministic, or mediated by an estimator such as a language model |
| **Content class** | Holds references only, derived content, or recoverable content |
| **Rebuild** | Reproducible, approximable, or irreproducible |
| **Scope** | The tenancy and sensitivity envelope it inherits from its sources |

The last two matter most, and they are independent. The dangerous combination is state that **holds recoverable content and cannot be rebuilt** — a language-model summary whose model has since been retired, for instance. It survives the deletion of its source while still carrying that source's content, and it cannot be repaired after a correction without producing something materially new. Every genuinely hard case lives there.

Scope is inherited, not chosen. A projection over tenant-scoped memory is tenant-scoped whether or not the storage engine has ever heard of tenants.

## Stale is a relationship, not a flag

The obvious design is a `stale` boolean on each projection. It does not work, for a boring reason: a flag is only correct if something reliably sets it, and real substrates reliably do not. The **[substrate capability mapping](Runtime-Evidence)** found exactly this — embeddings, indices, and community summaries all exist, and none of them self-invalidate when their sources change.

So define staleness as something you *compute* instead, by comparing what the projection recorded about its sources against those sources now:

| State | Condition | What it means |
|---|---|---|
| **Current** | every source is at the version the projection recorded | safe to use |
| **Stale** | some source has changed since | content may be **wrong** |
| **Residual** | some source has been tombstoned or purged | content may be **prohibited** |

Three things follow, and they are why the relationship beats the flag.

**Nothing has to notify anything.** The check runs when the projection is read, which is where Agent Memory already puts recall governance. A substrate that never invalidates anything becomes governable without modifying the substrate.

**Stale is not an error.** Using a stale projection is often perfectly reasonable. Using one *without recording that it was stale* is not. Staleness belongs in the admission decision and the receipt, not in a background job whose purpose is to briefly make the flag true.

**Stale and residual are different problems.** Staleness is a correctness problem, and recomputation may fix it. Residue is a governance problem, and only the deletion authority may fix it. Treating both as "invalid" throws away the distinction the whole architecture exists to protect.

## When correction and deletion give opposite orders

Agent Memory prefers preserved history to silent overwrite, so when a memory is corrected, the old version of a derived summary is normally kept — otherwise you destroy the evidence of what earlier decisions were actually based on.

Deletion wants the opposite. That retained old version is, once its source is purged, precisely the recoverable content the deletion was supposed to eliminate.

```text
correction says:  keep the superseded projection, it is evidence
deletion says:    destroy the superseded projection, it is residue
```

This is a real conflict, not a modelling mistake, and it has to be resolved by stated precedence rather than discovered in production. The spike sets **deletion dominant**: reconstructability degrades to content-free evidence — receipts, hashes, tombstones — which is the tradeoff **[Lifecycle and Forgetting](Lifecycle-and-Forgetting)** already contemplates for the tension between audit and erasure.

Purge scope is the *transitive* closure. Projections are routinely built from other projections, and stopping after one hop is how residue survives.

## Rebuilding is a governed mutation

The least obvious finding, and the one most likely to be built wrong.

When a projection's transform involves a language model, rebuilding it does not restore anything. It **commits new content**. So if detecting staleness is allowed to trigger a rebuild automatically, an estimator has acquired the ability to write into memory whenever it can cause a version bump — which is the confidence-becomes-authority failure with a maintenance job in front of it, structurally identical to the authority-laundering case in **[Security and Privacy](Security-and-Privacy)**.

```text
prohibited   staleness detected → model recomputes → content committed
required     staleness detected → rebuild proposed → governance decides
                                → permitted action → committed → receipt
```

Deterministic rebuilds are the exception that proves the rule. They can be authorized in advance as a class, precisely because their output is a function of canonical state rather than of a model's disposition on the day.

## Measuring residue honestly

The measurement is not a volume. It is a partition, and one cell has to be empty:

| Bucket | Meaning |
|---|---|
| **Purged** | demonstrated removed |
| **Declared residual, controlled** | known to survive, reported, still reachable |
| **Declared residual, uncontrollable** | known to survive, reported, out of reach — exports, third-party copies, model weights |
| **Undeclared residual** | survives, and nobody said so |

**Undeclared residue must be zero.** It is a disqualifying gate, not a score to average away: a deletion that leaves recoverable content it never reported is a failed deletion regardless of how much it correctly removed.

Two rules keep the measurement honest. State that cannot be enumerated goes in the *uncontrollable* bucket — declared and reported — rather than being quietly omitted because it was hard to find. And undeclared residue is found by an independent sweep over the derivation graph, never by asking the deletion process whether it finished. A purge that reports no residue because it only looked one hop deep has measured its own optimism.

## Where this sits

This slice exists because ADR-020's proof bar requires that derived-memory deletion residue be *tested*, and that single line sits on top of everything above. The bar was fixed before the implementation that had to clear it, and all seven of its items now execute: a declaration surface for tier-3 state, freshness computed as a relation rather than a flag, correction that supersedes without erasing, a transitive purge, an independent sweep that catches a one-hop purge, and refusal of automatic estimator-mediated rebuild. ADR-020 is now Accepted; clearing this one bar was one of its validation items, not the whole acceptance.

## Canonical sources

- Design spike: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/programs/runtime-evidence/canonical-and-derived-state.md
- Retention, deletion, tombstones: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/28-retention-deletion-and-tombstones.md
- Recovery and replay: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/31-recovery-rollback-and-replay.md
- Substrate capability mapping: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/programs/runtime-evidence/graphiti-conformance.md

## Next

- **[Lifecycle and Forgetting](Lifecycle-and-Forgetting)** for the forgetting operations this refines
- **[Security and Privacy](Security-and-Privacy)** for deletion residue as an attack surface
- **[Runtime Evidence](Runtime-Evidence)** for the evidence bar these paths are measured against
