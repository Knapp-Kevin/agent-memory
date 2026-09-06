# Future Subsystem: Memory Compiler

**Status: future subsystem. Not a core component.** This note exists because the prerequisite guardrails now exist — the threat model ([`../15-memory-threat-model.md`](../15-memory-threat-model.md)), source trust ([`../16-source-trust-and-reputation.md`](../16-source-trust-and-reputation.md)), conflict resolution ([`../17-conflict-resolution-engine.md`](../17-conflict-resolution-engine.md)), schema evolution ([`../27-schema-registry-and-type-evolution.md`](../27-schema-registry-and-type-evolution.md)), and interoperability profiles ([`../35-interoperability-profiles.md`](../35-interoperability-profiles.md)). Promotion into the component architecture still requires its own ADR and conformance surface.

## Concept

A memory compiler converts existing artifacts into memory units at scale: docs, traces, issues, PRs, decisions, chat transcripts, code-graph outputs. The appeal is obvious — most of an organization's memory already exists as artifacts nobody governs. So is the risk: a compiler is a bulk-ingestion channel, and bulk ingestion is the threat model's front door.

## Ingestible source types

A compiler may ingest, in decreasing order of default trust (classes per doc 16):

```text
signed / verified artifacts        code graphs, certified records, receipts
deterministic tool observations    build outputs, test results, traces
authoritative documents            policies, ADRs, decision records
organizational documents           issues, PRs, design docs, wikis
conversational material            chat transcripts, meeting notes
external documents                 anything crossing the organization boundary
```

Each compiled unit records its source type; a compiler must not flatten this ladder into "ingested."

## Required source trust checks before compilation

- Every source resolves to a source class and trust estimate per doc 16 **before** unit generation; unattributable material compiles only into `unknown/unattributed`-classed memory, which is barred from durable promotion.
- Independence checks apply across the batch: a thousand artifacts echoing one origin are one source (the manufactured-corroboration trap at compile scale).
- External and conversational sources pass sensitivity classification ([`../19-privacy-and-sensitivity-classifier.md`](../19-privacy-and-sensitivity-classifier.md)) at ingest; uncertain sensitivity compiles conservatively.
- Compilation of policy-shaped or decision-shaped content produces *candidate* records only — never active policies ([`../36-policy-as-memory.md`](../36-policy-as-memory.md)) or binding decisions ([`../profiles/durable-decision-memory-profile.md`](../profiles/durable-decision-memory-profile.md)) without their full authority paths.

## Provenance preservation

Compiled memory preserves, per unit: source ref (retrievable original), compiler identity and version as the observing estimator (`estimator_ref`/`estimator_version`), extraction method, compile-time trust and sensitivity estimates with uncertainty, and batch lineage (which run, which corpus). A compiled summary keeps refs to the passages it summarizes — compilation is exactly the summarization-provenance risk of `04-governance-and-pama.md` at industrial volume.

## Certification boundaries for compiled durable memory

```text
compiler output -> transient/observed memory, evidence-linked   (allowed)
compiler output -> candidate proposal via calibrated scoring    (allowed, trap-tested)
compiler output -> certified or crystallized memory             (never directly)
```

Certification of compiled memory requires everything certification always requires, plus: the certifier evaluates the *source*, not the compiler's confidence in its extraction; batch certification ("this corpus is trusted, certify all units") is authority laundering and prohibited; and compiled units carry a compiled-origin marker permanently, so a later dispute can recall the entire lineage.

## Promotion criteria into core

The compiler becomes a core component only when: an ADR proposes it with a bounded contract; the compiler adapter is specified against [`../34-adapter-contracts.md`](../34-adapter-contracts.md); poisoning-at-scale fixtures exist (batch spam, manufactured corroboration, compiled-policy injection); and at least one implementation demonstrates governed compilation under Profile 1 evidence.
