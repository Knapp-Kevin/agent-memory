# Memory-Native Logical State Algebra Pressure Test

Status: **completed exploratory research** for #276.

Final disposition: [`no_new_algebra`](memory-native-logical-state-algebra-closeout.md).

This document records the pressure test that led to the closeout. It is not canonical doctrine and does not authorize a new storage engine, schema, transition algebra, or ADR.

## Research question

Does Agent Memory need a new memory-native logical state-transition algebra above replaceable physical persistence, or do the existing lifecycle, derivation, currentness, isolation, PAMA, maintenance, evidence, and component contracts already supply the required logical layer?

The burden of proof was deliberately placed on the new abstraction:

```text
new abstraction
must prove missing reusable semantics
not merely rename existing operations
```

The tested evidence did not meet that burden.

## Evidence boundary

The pressure test started from completed cross-architecture research rather than blank-sheet design. That work had already reproduced the same governance distinctions across file/document, linked-note, lexical, vector, knowledge-graph, temporal-graph, GraphRAG, event-log, relational/document, hierarchical, shared/distributed, opaque learned/latent, and hybrid families.

The durable findings include:

```text
identity != truth
retrieval != recall admission
relevance / reachability != permission
derived state != canonical authority
historical integrity != current truth
storage placement != authority
shared membership != mutation authority
delete operation != forgetting completeness
probabilistic / learned influence != durable write authority
```

A new logical algebra therefore had to improve portability, correctness, recovery, or implementation clarity beyond those already-shared contracts.

## Existing primitive inventory

The candidate responsibilities were mapped to existing Agent Memory surfaces before any new vocabulary was promoted.

| Candidate logical responsibility | Existing Agent Memory surface | Result |
|---|---|---|
| stable logical identity | memory-unit identity, source/evidence identity, optional content-reference profiles | already represented |
| source provenance / derivation | provenance doctrine, derivation evidence, output custody | already represented |
| derived-state currentness | derivation currentness | already represented |
| correction / dispute / supersession | lifecycle, temporal causality, correction/supersession doctrine | already represented |
| reinforcement / weakening | estimator/scoring evidence | represented, intentionally not authority |
| promotion / crystallization | lifecycle + PAMA | already represented |
| consolidation / summarization / semanticization | derived-state doctrine + maintenance evidence | already represented |
| projection rebuild / invalidation | derivation currentness + maintenance evidence | already represented |
| deletion / forgetting / purge | lifecycle/deletion doctrine + residue evidence | already represented |
| scope / isolation | isolation-domain doctrine and crossing rules | already represented |
| concurrent/conflicting mutation | conflict/concurrency evidence + PAMA consequence boundary | represented; physical transaction mechanics remain backend-specific |
| autonomous maintenance transaction | maintenance-run evidence | already represented |
| learned / predictive influence | conditional-memory influence + governed uncertainty | already represented |
| mutation/action authority | PAMA | already represented and separate from operation naming |
| portable governance evidence | receipt/evidence profiles | already represented |
| component optionality | capability/component program #274 | implemented without a new state algebra |

The proposed verbs therefore mapped cleanly to existing contracts:

```text
observe / ingest
  -> identity + provenance + proposal/commit evidence

link / derive
  -> derivation + currentness + custody

revise / correct / challenge / supersede
  -> lifecycle + temporal causality

reinforce / weaken
  -> estimator/scoring evidence, no authority effect by itself

consolidate / summarize / semanticize
  -> derived state + maintenance transaction + validation

promote / crystallize
  -> lifecycle transition + PAMA

invalidate / mark stale
  -> lifecycle/currentness

rebuild projection
  -> derivation currentness + maintenance transaction

forget / delete / purge
  -> deletion consequence + transitive residue/lifecycle satisfaction

predict / influence
  -> conditional-memory influence gate

re-evidence / revalidate
  -> currentness/evidence transition
```

This is evidence against creating a second parallel lifecycle model merely to collect existing semantics under another namespace.

## Cross-substrate mapping

The same correction scenario was mapped across three materially different persistence families:

```text
source S1 is current
-> derived state D1 is built from S1
-> S1 is corrected to S2
-> D1 remains physically present
```

The required logical outcome is independent of substrate:

```text
S1 remains historical evidence where policy permits
S2 becomes current
D1 becomes stale / rebuild-required
D1 physical presence does not imply currentness
D1 may not regain authority from retrieval usefulness
rebuild produces a new derived identity/evidence chain
```

### Relational/document

Strong transactions and explicit version columns help with canonical updates, but successful canonical transaction completion does not automatically invalidate every embedding, cache, summary, or other external projection. Physical row identity also does not become stable Agent Memory logical identity.

Existing currentness, derivation, and lifecycle contracts express the distinction.

### Knowledge/temporal graph

Graph reachability and temporal relationships can make lineage inspectable, but an inferred edge/path may remain physically reachable after its source basis changes. Reachability is neither currentness nor permission, and graph deletion may leave other projections or caches.

Existing derivation, currentness, isolation, and admission contracts express the distinction.

### Event log / ledger

Append-only history naturally preserves mutation sequence, but historical integrity does not determine current truth. Tombstone/delete events do not prove transitive forgetting, and a valid checkpoint advance does not prove retrieval behavior remained semantically acceptable.

Existing temporal, currentness, deletion, and evidence contracts express the distinction.

## Executable pressure evidence

PR #277 added `logical-state-algebra-scenarios.json`, the reference pressure harness, focused tests, and `.github/workflows/logical-state-algebra-pressure.yml`.

The dedicated workflow passed at exact research head:

```text
head: 9f6bdbc415afdf57823d806312c33bd833cd1cb6
run:  31800258733
result: success
```

The research foundation merged in PR #277 as `767d8b7391de08892daaab9847b938bc7992f19c`.

## Later implementation pressure

The leading `no_new_algebra` hypothesis remained falsifiable after PR #277. Subsequent #274 implementation work supplied the required pressure rather than merely accepting the research conclusion on paper.

PR #297 implemented component/capability declarations, maturity, deterministic provider resolution, explicit ambiguity/shortfall failure, and a governed procedural-memory vertical slice without requiring a new state algebra.

PR #299 / completed #298 established the version-bound component adapter and qualification contract without introducing a second lifecycle/state model.

PR #302 then exercised two materially different real code-graph providers through the shared qualification surface. Its first failed run exposed two concrete implementation defects:

1. CodeGenome retained a cross-file semantic-resolution collision after earlier target-file repair. The provider was repaired in CodeGenome #12 / PR #13 by preserving file identity in symbol and caller-span resolution.
2. Agent Memory's Graphify normalizer expected `edges`, while Graphify's native NetworkX node-link artifact uses `links`. The normalizer was corrected to the real provider shape.

Neither failure exposed a missing universal memory-state primitive. The existing qualification/currentness/evidence contracts were sufficient to detect the mismatch, preserve it as evidence, refuse an unearned qualification, repair the responsible layer, and re-run the exact-version proof.

That is material evidence for `no_new_algebra`, not merely absence of imagination.

## External pressure signal

Agent Manifest #298 provides an independent counterexample to treating state-transition integrity as semantic correctness:

```text
state-transition integrity
!= semantic/retrieval behavior
!= lifecycle correctness
!= downstream authority
```

This strengthens the separation already represented by Agent Memory's currentness, lifecycle, admission, authority, and evidence surfaces. It does not establish a need for a new algebra.

## Evaluated outcomes

### A. `no_new_algebra`

**Selected.** Use the existing lifecycle, derivation/currentness, isolation, PAMA, maintenance, evidence, and component/qualification contracts directly.

### B. `narrow_transition_contract`

**Not currently required.** Reconsider only if at least two materially different component families repeatedly require the same transition/evidence envelope and the incompatibility causes a real correctness, recovery, interoperability, or evidence problem.

A possible future envelope would bind:

```text
requested transition
+ target logical identity
+ source/currentness basis
+ scope/isolation basis
+ estimator evidence, if any
+ PAMA decision
+ backend transaction result
+ post-write validation
+ lifecycle result
+ reconstructable receipt
```

That would be an orchestration/evidence contract, not a database engine or new authority model.

### C. `profile_specific`

**Not required as the primary conclusion.** Backend-specific mechanics remain explicit in component/capability profiles where necessary, without creating competing Agent Memory semantic models.

### D. `stronger_engine`

**Rejected for lack of evidence.** No tested case requires Agent Memory to build a new database-like state runtime, uniform WAL/MVCC layer, universal conflict engine, or storage-specific transaction system.

## Future falsification trigger

Reopen this question only if implementation demonstrates a recurring requirement that current contracts cannot faithfully express, such as:

- cross-component atomic logical transitions required for correctness;
- uniform durable conflict/reconciliation semantics that cannot remain backend/profile specific;
- recovery/replay semantics that must be shared across materially different substrates;
- shared logical versioning that cannot safely remain represented through current identity/currentness contracts;
- lifecycle closure spanning several physical modules in one indivisible governed transaction.

Until then:

```text
recommendation = no_new_algebra
new ADR = not warranted
new physical persistence engine = not warranted
```

See [`memory-native-logical-state-algebra-closeout.md`](memory-native-logical-state-algebra-closeout.md) for the final issue-closeout statement and evidence boundary.
