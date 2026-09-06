# Agent Memory Atlas research intake

Issue: #306
Parent research program: #304

This directory defines the reproducible intake and synthesis boundary for research based on `neoneye/agent-memory-atlas`. Atlas is used as a source index and hypothesis generator, not as doctrine authority or runtime conformance evidence.

## Frozen source boundary

The initial snapshot is:

```text
repository: neoneye/agent-memory-atlas
commit: 90bfeed14764e268c82c925d4c39645c7480d015
root tree: 70dfb11b65863e0af98c7b32387eb2837ab02a8c
content tree: 9b98810d489c7aa4526d8e6d8005d60a351cfebe
systems tree: c7695782e17e3b17143267e671d064917d57ed0c
```

`snapshot-manifest.json` records the verified Git object identities used by the intake. The rendered web site is not a count or identity authority.

## Research pipeline

```text
Atlas report
  -> snapshot-bound inventory record
  -> deduplicate against current Agent Memory surfaces
  -> classify independent triage dimensions
  -> verify consequential claims against primary source
  -> reproduce when consequence warrants it
  -> record support / contradiction / narrowing / unresolved result
  -> only then promote a bounded follow-on
```

A high Atlas mark count is never a promotion criterion.

## Machine-readable records

- `snapshot-manifest.json`: immutable identity and pinned-source metadata for this intake.
- `report-inventory.lock.json`: committed reconstruction lock for the normalized 283-record inventory, including exact record count and SHA-256.
- `report-inventory.jsonl`: deterministic generated output of `scripts/build_atlas_research_inventory.py`. It is intentionally not committed; CI regenerates it from the exact pinned Atlas checkout and refuses output that does not match `report-inventory.lock.json`.
- `claim-ledger.jsonl`: independently verified or deliberately unresolved consequential claims. This is not generated from prose automatically.
- `deduplication-map.json`: likely findings mapped to existing Agent Memory owners before new work is created.
- `corpus-synthesis.json`: #304 completion record containing the exact seven-mechanism mapping, all 21 pattern dispositions, benchmark/candidate decisions, Agent Memory self-audit reconciliation, promotions, rejections, and completion flags.
- `corpus-synthesis.md`: human-readable explanation of the bounded research closeout.
- `schemas/`: research-record schemas. These schemas describe research infrastructure, not canonical runtime state.

The generated Actions artifact is convenience evidence, not the durable identity boundary. It may expire. Durable reconstruction is provided by the pinned Atlas source identity + committed generator + committed inventory lock. This avoids checking in half a megabyte of regenerated secondary-source metadata while still making silent inventory drift fail closed.

## Inventory extraction boundary

The inventory extractor intentionally limits automatic extraction to report frontmatter plus exact file/blob identity. It does not scrape `Steal`, `Avoid`, or narrative sections into Agent Memory. Those fields remain empty until a bounded claim is independently summarized and verified.

This avoids turning a research index into a copied secondary-source corpus.

For the pinned snapshot, the canonical generated inventory has:

```text
records: 283
sha256: 4573f48dc220948f46c97aa3669e77da8b130ca966007f63876592c16535dc5a
```

CI must reproduce both values before the inventory is accepted.

## Triage dimensions

Triage is categorical and must not be collapsed into one score:

```text
novelty: none | low | medium | high
failure_severity: low | moderate | high | catastrophic
transferability: category_local | architecture_local | representation_neutral
verifiability: prose_only | source_checkable | executable | benchmarked
execution_cost: trivial | low | medium | high
component_value: none | reference | comparator | qualification_candidate
research_priority: skip | reference | verify | deep_review
```

These dimensions answer different questions. A representation-neutral catastrophic risk is not made equivalent to an easy-to-run comparator by arithmetic.

## Research batches

The frozen #304 execution order was:

1. self-audit calibration against Atlas's Agent Memory report;
2. seven-mechanism crosswalk;
3. design-pattern disposition;
4. benchmark/evaluation audit;
5. architecture-stratified system review;
6. comparator and component candidate selection;
7. synthesis and bounded promotion decisions.

The corpus review is not alphabetical and completion is not defined as identical depth for all 283 reports.

## Frozen deep-review questions

Every deep-reviewed system answers the same questions:

1. What retained state does the system actually treat as memory?
2. What is canonical versus derived or cached?
3. Who or what may create, mutate, correct, supersede, delete, or promote it?
4. How are evidence, confidence, trust, and authority separated or conflated?
5. What happens after correction when the rejected value is encountered again?
6. What happens after deletion when background work or rebuild runs again?
7. What scope, tenant, or project boundary is mechanically enforced on read, write, derivation, and rebuild?
8. What negative assertions prove forbidden material does not surface or influence?
9. What provenance survives extraction, summarization, graph construction, or consolidation?
10. What operational costs and lag are introduced on write, read, and maintenance paths?
11. What survives restart and what depends on process-local state?
12. Which failure modes are observable versus silent?
13. Which mechanism is genuinely reusable outside this implementation?
14. What exact claim would an Agent Memory fixture or comparator falsify?
15. What should Agent Memory not copy from this system?

Changing this question set requires an explicit methodology revision rather than a silent edit.

## Promotion and stopping rule

Create a follow-on only when a verified claim exposes at least one of:

- a distinct correctness or governance failure not already covered;
- a reusable implementation mechanism with a clear Agent Memory owner;
- a falsification fixture that can strengthen an existing guarantee;
- a component capability worth qualification under #280;
- a representation-neutral contradiction that current doctrine cannot express.

Otherwise record `covered`, `reference`, `rejected`, `not_relevant`, or `unresolved` and stop.

The expected ADR result remains `none` unless verified evidence proves a doctrine-level gap.

## #304 synthesis boundary

`corpus-synthesis.json` is intentionally narrower than a claim that every Atlas report was independently reproduced. It records the converged research result under the stopping rule above:

```text
283 snapshot-bound inventory records
7/7 Atlas mechanisms mapped
21/21 Atlas patterns disposed
primary-source benchmark/candidate shortlist
Agent Memory Atlas-report reconciliation
bounded promotion(s)
explicit rejection/no-action log
no new ADR
no Atlas-derived authority
```

`scripts/validate_atlas_research_synthesis.py` fails closed on missing or substituted mechanism/pattern IDs, duplicate entries, snapshot drift, incomplete completion flags, missing promotion/rejection evidence, or any authority/doctrine escalation.
