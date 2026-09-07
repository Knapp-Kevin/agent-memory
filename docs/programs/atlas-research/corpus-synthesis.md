# Agent Memory Atlas corpus synthesis

Issue: #304

Evidence boundary:

```text
Atlas:        neoneye/agent-memory-atlas@90bfeed14764e268c82c925d4c39645c7480d015
Agent Memory: f2fc966c403d7adf028c24240b85c6e4e576a25a
```

This document closes the bounded research program defined by #304. It does not claim equal-depth manual review of all 283 pinned reports. The complete corpus is covered at the reproducible inventory layer from #306/#322; deeper review was selected by distinct correctness, governance, architecture, benchmark, and component value. Primary-source verification was required before promotion.

The machine-readable controlling record is `corpus-synthesis.json`. CI requires its exact seven-mechanism and twenty-one-pattern sets.

## Snapshot result

The pinned Atlas source contains 283 system reports, 21 design patterns, and 7 rubric mechanisms. These are snapshot-scoped corpus counts, not ecosystem-prevalence statistics, product scores, or Agent Memory maturity targets.

Atlas remains a secondary-source index and hypothesis generator. Its code-reading marks do not establish runtime conformance, production fitness, component qualification, or authority.

## Seven-mechanism crosswalk

| Atlas mechanism | Agent Memory disposition |
| --- | --- |
| Rejected-value tombstone | Covered under different semantics by #147/#148 and semantic readmission evidence. |
| Explicit trust state | Covered under different semantics by multidimensional trust, evidence, truth/certification, and authority boundaries. |
| Bi-temporal validity | Covered by temporal doctrine and reference/runtime evidence. |
| Scope enforced in retrieval | Covered more broadly across read, write, derivation, rebuild, and external-scope bridging. |
| Append-only mutation audit | Covered by audit-event and portable evidence surfaces. |
| Human review surface | PAMA supports required review semantics; no canonical end-user review UI is claimed. |
| Negative retrieval assertion | Covered more broadly by must-not-surface and must-not-influence lifecycle evidence. |

No mechanism required new core doctrine on this pass.

## Pattern disposition

All 21 patterns from the pinned Atlas index have explicit dispositions in `corpus-synthesis.json`.

The resulting groups are:

- already covered by existing Agent Memory doctrine/evidence;
- covered under different or broader semantics;
- useful for adversarial fixture hardening;
- optional component/deployment guidance;
- optional product guidance;
- reference-only architecture evidence.

Atlas labels remain provenance. They do not become Agent Memory terminology merely because they appear in the research record.

## Verified comparator set

The ranked systems were selected for distinct failure/capability value, not popularity or Atlas mark count:

1. Claude-Mem: canonical SQLite state before later Chroma synchronization; used to pressure #308/#282.
2. Verel: rejected-value semantic re-entry adversarial fixtures.
3. AgentRecall-X: bounded authority-quality/reliability-decay comparator; its threshold is not Agent Memory doctrine.
4. Memory Engine: least-permissive principal/access composition on the inspected path.
5. Graphiti: validity-time versus record-time temporal graph representation.
6. Nanobot: durable background progress/cursor advancement after completed success, without an exactly-once claim.
7. Basic Memory: editable canonical files plus rebuildable derived state; reference-only at the pinned AGPL-3.0 rights posture.
8. Memanto: explicit conflict dispositions, with no need for another conflict engine beyond #12.

This list is not an adapter backlog.

## Benchmark audit

Primary-source review narrowed several benchmark claims:

- MemoryAgentBench FactConsolidation measures newest-fact/current-answer preference, not selective forgetting.
- GoodAI LTM performs reset after the scored example, so reset is not forgetting evidence.
- PersistBench pressures cross-domain leakage, sycophancy, and beneficial memory use; it is not a deletion benchmark.
- ForgetEval provides a useful supersede/release/purge control-plane test shape but does not establish Agent Memory transitive residue or post-background resurrection guarantees.

Existing #138 and conformance owners remain controlling.

## Promoted operational gap

One representation-neutral operational distinction survived deduplication:

```text
write accepted
!= canonical durable
!= required derived state current
!= governed recall current-visible
!= context current-visible
!= settled
!= quiescent
```

That became #308 and was subsequently implemented, with restart obligations composed into #282. Claude-Mem and Nanobot supplied materially different external pressure for the same boundary. No separate ADR was required.

## Agent Memory self-report reconciliation

Atlas analyzed Agent Memory at `bba0aa4cab8e04d11f5380b215b3eea6998fe119` on 2026-08-11. Current disposition at `f2fc966c403d7adf028c24240b85c6e4e576a25a` is:

| Atlas-era observation | Current disposition |
| --- | --- |
| Rejected-value tombstone gap | Fixed by #147/#148 and semantic readmission evidence. |
| No discrete Atlas-style trust state | Not established as a defect; Agent Memory intentionally uses broader trust/evidence/authority semantics. |
| Reference substrate is not a production memory service | Still true by design, with reference claims bounded and real external runtime evidence tracked separately. |
| No committed run outputs under `reports/` | Partially valid but narrowed; exact-head workflow evidence and durable locks now exist outside that directory. |
| No dependency manifest | Fixed; current root has `pyproject.toml` and reference dependencies are declared in `reference/requirements.txt`. |
| README/generated-count drift | Historical only until freshly measured; old counts are not carried forward as a current defect. |

## Rejection and no-action log

The research explicitly rejects:

- Atlas mark count as an Agent Memory maturity score;
- equal-depth review of all 283 systems solely to claim exhaustiveness;
- an Atlas trust enum as a mandatory core field;
- a new conflict engine from Memanto;
- Basic Memory as a default dependency without deliberate AGPL source-rights posture;
- one adapter for every interesting Atlas system;
- a new ADR solely because Atlas named a pattern.

## Completion boundary

#304 is complete when exact-head validation confirms that the pinned inventory remains reproducible, all seven mechanisms and all 21 patterns remain represented, promoted findings stay evidence-bound, rejected findings stay recorded, and the synthesis retains `authority_effect = none` plus `doctrine_disposition = no_new_adr`.

Completion means the research question converged under the frozen stopping rule. It does not mean every repository received identical attention.
