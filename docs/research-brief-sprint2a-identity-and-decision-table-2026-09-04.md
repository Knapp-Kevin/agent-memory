# Research Brief: Sprint 2a — substrate identity collision and decision-table completion

**Date**: 2026-09-04
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 2 of the governed loop.
**Scope locked to**: GAP-SEC-08 and GAP-ARCH-09 from `docs/RESEARCH_BRIEF.md` Sprint 2.

## 1. Why this slice, and why not all of Sprint 2

Sprint 2 carries seven gaps and is estimated at 5 days on the additive/warn-first path the owner selected (host authenticates recall principals; adapter records). Attempting it as one governed cycle would put GAP-SEC-02's authority-record work, GAP-ARCH-04's 82-site `Proposal` blast radius, and two mechanically-contained defects into a single audit verdict, where a VETO on any one blocks all seven.

GAP-SEC-08 and GAP-ARCH-09 are the two members of Sprint 2 with **zero external blast radius** and machine-checkable success criteria. They are lifted into their own cycle. The authority-record leg (GAP-SEC-02 + GAP-ARCH-18) is Loop 3; the artifact-trust leg (GAP-SEC-03 + GAP-SEC-04) is Loop 4; GAP-ARCH-04 is Loop 5.

This does not reorder Sprint 2's dependencies: the deep-audit brief records that Sprint 2 must precede Sprint 4, and nothing inside Sprint 2 depends on SEC-08 or ARCH-09.

## 2. Verified findings

### F1 — GAP-SEC-08 confirmed, and materially more severe than recorded

The deep audit recorded "cross-tenant fact overwrite". Reproduced end to end (`probe_sec08c.py`): two `GovernedMemoryAdapter` instances for different tenants over one `InMemoryTemporalGraph`.

```
A committed: ... fact_uuid='ref-0004'  receipt_id='ref-0006'  correlation_id='ref-0001'
B committed: ... fact_uuid='ref-0004'  receipt_id='ref-0006'  correlation_id='ref-0001'

facts surviving in the shared substrate: 1 (two tenants each wrote one)
   ref-0004 | group_id=tenant-B | 'tenant B value'
substrate write_log: [('write_fact', 'ref-0004'), ('write_fact', 'ref-0004')]

tenant A's fact still present: False
```

**It is not only the fact uuid.** Every identifier minted by the adapter collides: the fact uuid, the decision `receipt_id`, the `correlation_id`, and all four event ids (`memory.propose`, `memory.authorize`, `memory.commit`, `memory.receipt`). Two tenants therefore emit decision receipts claiming the same `receipt_id` and event streams claiming the same `correlation_id`.

So the blast radius is not storage alone — it is the **evidence surface**. Receipt correlation, event causation chains, and any downstream consumer that joins on `receipt_id` or `correlation_id` silently merge two tenants' governance records. Both adapters report `committed=True` and neither raises.

**Mechanism** (unchanged from the audit): `adapter.py:121` constructs `DeterministicIds("ref")` per adapter instance; the counter is instance state (`substrate.py:33-39`). `substrate.py:106-109` `write_fact` is `self._facts[fact.uuid] = fact` — a dict assignment, so a colliding uuid replaces silently.

A shared substrate is the normal deployment shape for the Graphiti port, so this is a default-configuration defect, not a misuse.

### F2 — GAP-ARCH-09 confirmed, with the exact per-cell drift

`_BASE_TABLE` (`policy.py:53-95`) covers 10 operations. `docs/33-pama-decision-table.md:80-93` defines 12. The three missing are `score_adjustment`, `link_creation`, `link_deletion`, and `_base_outcome` (`policy.py:151`) falls back to `REQUIRE_REVIEW` for all of them.

The fallback is not uniformly conservative. Per cell, against doctrine:

| Operation | Risk | Doctrine | Fallback | Drift |
|---|---|---|---|---|
| score_adjustment | low | allow_with_ledger | require_review | stricter |
| score_adjustment | medium | allow_with_ledger | require_review | stricter |
| score_adjustment | high | require_review | require_review | same |
| score_adjustment | critical | **block** | require_review | **WEAKER** |
| link_creation | low | allow_with_ledger | require_review | stricter |
| link_creation | medium | allow_with_ledger | require_review | stricter |
| link_creation | high | require_review | require_review | same |
| link_creation | critical | require_review | require_review | same |
| link_deletion | low | allow_with_ledger | require_review | stricter |
| link_deletion | medium | require_review | require_review | same |
| link_deletion | high | require_review | require_review | same |
| link_deletion | critical | **require_external_verification** | require_review | **WEAKER** |

Two cells resolve weaker than doctrine, five stricter, five identical. The audit named the `score_adjustment/critical` case; `link_deletion/critical` is the second and was not previously called out.

### F3 — Blast radius is zero

`_BASE_TABLE` is private with three references, all inside `policy.py` (`:53`, `:151`, `:178`). The strings `score_adjustment`, `link_creation`, and `link_deletion` appear in **no Python file in the repository**. The schema enum already admits all three, so no schema change is required and no fixture carries them. Adding the twelve cells cannot change the outcome of any existing call.

### F4 — New drift, opposite direction

`domain_schema_mutation` has a row in `_BASE_TABLE` and four occurrences in `schemas/pama-decision.schema.json`, and is defined in `ADR-032` and two PAMA profiles — but it has **no row in the `docs/33` base table**. So the doctrine table is itself incomplete relative to the schema, in the reverse direction from ARCH-09.

Not previously gap-tracked. It is a documentation defect, not a runtime one: the code's cells for it are stricter than the `REQUIRE_REVIEW` fallback would be, so nothing resolves weaker. Recorded here for the plan to decide whether docs/33 is in scope.

## 3. Design options for the plan

**SEC-08.** Three candidate repairs:

- **(a) Tenant-prefixed ids** (`DeterministicIds(f"ref-{tenant}")`). Rejected: changes the id *format*. **Correction (audit V5)**: the stated reason — "committed fixtures plus many tests assert literal `ref-000N` values" — is false. `grep -rn "ref-000"` returns 0 hits in `reference/tests/` and 0 in `fixtures/`. The rejection stands on the format change alone, and the absence of coverage is itself a finding: LD1's bit-identical claim had nothing pinning it.
- **(b) Substrate-owned counter** — the adapter asks the substrate for the next id. This is the correct end-state and is already scheduled: `docs/RESEARCH_BRIEF.md` Sprint 6 lists "substrate-scoped ids" under GAP-ARCH-02, and it requires extending `TemporalGraphPort`, which Sprint 4 owns. Doing it here would pull two later sprints forward.
- **(c) Collision refusal at the substrate boundary** — `write_fact` refuses a uuid that already exists with different content, raising rather than silently replacing. Additive, no id-format change, no protocol change, and it converts silent cross-tenant data loss into a loud failure at the exact point of harm.

**(c) was the recommendation at this point in the investigation — superseded by section 7.** The claim that (c) "stops the evidence-surface merge" is **wrong**: receipt and event ids never pass through `write_fact`. Left in place rather than rewritten so the correction is legible; read section 7 for the recommendation that stands.

Open question the plan must settle: whether refusal keys on differing `group_id` only, or on any differing content. `_write` always mints a fresh uuid within one adapter, so a same-adapter uuid is never legitimately rewritten; but `forbidden_hits.py:238` and `benchmark_security.py:49` call `substrate.write_fact` directly, and `graphiti_driver.py` has its own `write_log`. Those three call sites must be checked against whichever rule is chosen.

**ARCH-09.** Add the twelve missing cells to `_BASE_TABLE` verbatim from `docs/33`. No option space; the only decision is whether to also fix F4's doctrine gap in the same cycle.

## 4. Risk grade

**L3.** GAP-SEC-08 is a security control on the write path with a CRITICAL-adjacent consequence (cross-tenant data loss plus evidence-record merging), and the change makes a previously-silent path raise. GAP-ARCH-09 alone would be L1, but the cycle grade is the maximum of its members.

## 5. Verification available

- SEC-08: the probe above becomes a regression test — two tenants, one substrate, assert both facts survive and no identifier is shared.
- ARCH-09: a table-driven test asserting every `docs/33` cell resolves to the documented outcome, which also pins F1's two weaker cells.
- Whole-suite: 868 tests must stay green; any test that depended on the silent overwrite is a finding, not a fix-up.

## 6. Next

`/qor-plan`.

## 7. Addendum: option (c) is insufficient alone; option (b-lite) found

Written after section 3 and superseding its recommendation.

**Option (c) does not fix the evidence-surface collision.** `receipt_id`, `correlation_id`, and the four event ids never pass through `substrate.write_fact` -- they are minted from the same counter but stored on the `CommitResult`. A collision guard on `write_fact` therefore stops the fact overwrite and leaves two tenants still emitting receipts and event chains under identical ids. Recommending (c) alone would have closed the data-loss half of F1 and silently left the half that F1 newly established.

**Option (b-lite): substrate-owned counter with graceful fallback.** The adapter draws ids from the substrate when the substrate offers a counter (`getattr(substrate, "next_id", None)`), and from its own `DeterministicIds` otherwise. This:

- fixes the collision at its source, for facts, receipts, **and** events;
- changes no id format, so no fixture or test literal moves;
- is bit-identical for the single-adapter case, because a substrate-owned counter starting at zero with one consumer emits exactly the sequence the per-adapter counter emits today;
- requires **no change to the `TemporalGraphPort` Protocol**, because the capability is discovered by attribute rather than declared -- so `graphiti_driver` and any external implementation keep working untouched, and Sprint 4's protocol extension stays Sprint 4's.

The only observable change is that two adapters sharing a substrate now interleave ids instead of colliding, which is the defect being fixed.

**Both, not either.** (b-lite) fixes the cause; (c) remains worthwhile as defence in depth, because it catches any path that still mints a duplicate -- including a foreign substrate with no `next_id` that falls back to per-adapter counters. Verified safe: `write_fact` is called only for genuinely new facts. `invalidate_fact` mutates `_facts` directly (`substrate.py:116`) and `restart_runtime.py:157` restores by assigning `substrate._facts` wholesale, so neither restore nor supersession passes through the guard. The two direct external call sites use explicit non-`ref-` uuids (`fh:derived-residue`, `foreign-benchmark-fact`) and cannot collide.

**Revised recommendation**: implement (b-lite) as the fix and (c) as the guard. (b) proper -- a declared `TemporalGraphPort` method and substrate-scoped id semantics -- remains Sprint 6 under GAP-ARCH-02, unchanged.
