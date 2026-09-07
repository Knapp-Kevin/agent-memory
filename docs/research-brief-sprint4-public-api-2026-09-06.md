# Research Brief: Sprint 4 — the public consumer API, measured against PRD-001 R1

**Date**: 2026-09-06
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 20.
**Implements**: issue #362 (deep-audit GAP-ARCH-01), after the ideation record at `.qor/gates/2026-09-06T2140-f7a9c3/ideation.json` (readiness `research_required`)
**Scope**: what the public surface is today, what PRD-001 R1 requires of it, how far the JS runtime diverges, and what each candidate shape costs. This brief measures; the three contract decisions remain the operator's.

## 1. What PRD-001 actually requires

#362 cites PRD-001 for "propose / decide / approve / commit as distinguishable stages". The requirement is larger. `docs/prd/PRD-001-configurable-agent-memory-runtime.md:115-130`, R1 "Stable Agent Memory API", lists **ten bounded operations** and then: "The API must distinguish proposal, decision, approval, commit, retrieval candidate, recall admission/activation, action authority, and execution evidence where those stages exist" -- **eight stages**, not four.

## 2. The surface today, mapped to R1

| R1 operation | Exists as | Where | Public-contract status |
|---|---|---|---|
| propose memory | fused into `commit_proposal(proposal, fact_text, ...)` | `runtime/adapter.py:178` | no separate stage; `Proposal` dataclass (27 fields, `core/policy.py:121`) unversioned |
| commit governed mutation | `commit_proposal` | same | `CommitResult` dataclass (`adapter.py:77`) unversioned; its `receipt`/`pama_decision` dicts are schema-backed |
| correct/supersede | `commit_proposal` with `operation="correction"`; `record_correction`, `mark_disputed` | `adapter.py` | as above |
| recall current admissible memory | `governed_recall(query, context)` | `adapter.py` | `RecallContext` (`:102`) and `AdmissionResult` (`:88`) unversioned; per-candidate decisions schema-backed |
| retain/version/activate procedural memory | `procedural_memory.reference_procedural_component`, `apply_action_governance`, `record_runtime_execution` | `memory/procedural_memory.py` | module functions; no envelope |
| inspect history/provenance | `rejected_value_history`, `tombstoned_ids`, substrate `write_log` | `adapter.py`, `state/substrate.py` | ad hoc |
| request forgetting/deletion | `governed_delete`, `tombstone` | `adapter.py` | `CommitResult`-shaped; tombstones unversioned |
| inspect decision/receipt evidence | `receipts.build_receipt`, `verify_receipt_decision_pair`, `build_audit_event` | `core/receipts.py` | outputs schema-backed (`decision-receipt`, `pama-decision`, `memory-audit-event`) |
| inspect component/capability posture | `doctor.diagnose`, `runtime_config.*` | `runtime/` | CLI-shaped; `runtime-configuration.schema.json` exists |
| inspect adapter/qualification posture | `qualification.qualification_from_adapter_results`, `discovery.run_probe` | `contracts/`, `runtime/` | schema-backed records exist (`component-capability-qualification`) |

Of the eight stages: **decision** (`Decision` -> `pama-decision.schema.json`), **commit** (receipt), **recall admission** (`contextual-recall-admission.schema.json`), and **execution evidence** (`execution-witness`, `derivation-evidence`) have boundary forms. **Proposal**, **approval**, **retrieval candidate** and **action authority** do not: a proposal is a dataclass, approval is either the removed assertion or the qualified-evidence discharge with no public entry point, a retrieval candidate is a string id inside `AdmissionResult.candidates`, and action authority lives in `procedural_memory.apply_action_governance`'s return.

## 3. Blast radius, by shape

| Surface | Count | Note |
|---|---|---|
| Files importing `GovernedMemoryAdapter` | 65 (33 tests, 32 non-test) | non-test: 25 in `agentmem_ref/`, 7 `run_*.py` |
| Files calling `commit_proposal` | 48 | the dominant seam |
| Files calling `governed_recall` | 26 | |
| Files calling `state_version` | 23 | consumers already read a version-shaped thing |
| Files calling `governed_delete` | 14 | |
| Files calling `current_fact_uuid` | 13 | |
| `RecallContext(` sites / `governed_recall(` sites | 50 in 27 files / 70 in 25 files | from #364 |
| `RestartSafeRuntime` / `ConfiguredRestartRuntime` | wrap `commit_proposal`, `governed_delete`, `checkpoint`, `recover`, `persist_visibility_snapshot` | a second Python surface over the same seams |

**Option A (schema-back the dataclasses as they are)** touches no call site but freezes 27 `Proposal` fields including the ADR-037 remnants (`review_satisfied`, `approval_refs`, `approves_own_authority`) as public contract. **Option B (small public surface, dataclasses internal)** touches no existing importer either -- the adapter keeps its methods and the envelope wraps them -- but every future consumer and both runtimes bind to the envelope; the migration of the 65 importers is optional and later, which is what makes B a freeze rather than a rewrite.

## 4. Versioning: what exists

46 of 58 schemas carry a `schema_version` property, mostly typed `string` without a constrained value; `contextual-recall-admission` pins `1.0.0`. ADR-030 already supplies the compatibility contract for projections consumed across a boundary: four states, `current` / `migration_required` / `incompatible` / `unknown`, and "serialization success is not semantic compatibility". A contract version on the public envelope should reuse that evaluation rather than add a parallel scheme (ideation assumption 5).

## 5. The JS runtime, measured

`integrations/agent-memory-runtime/src/index.mjs` exports `CONTRACT_VERSION '0.1'`, `ADAPTER_VERSION '0.1.1'`, and `createGovernedMemoryAdapter({storage, clock, ...})` returning `recall(request)` and `correct(request)` only (`:247-353`). Divergences from the Python reference, each concrete:

- **No PAMA.** `correct` admits on record state (`active`, not `disputed`/`superseded`, same scope) and commits; no `Proposal`, no `Decision`, no `require_review`.
- **Idempotency** the Python side lacks: `persistence.getCorrection(scope, idempotency_key)` replays a prior receipt; `commitCorrection` takes `expected_revision`.
- **Reason codes**: `invalid_record`, `missing_identity`, `unknown_scope`, `out_of_scope`, `disputed`, `superseded`, `state_<x>` versus the Python admission refusals recorded in `contextual-recall-admission`.
- **Receipt shape**: a `correction_committed` event with `prior_memory_id`, `replacement_memory_id`, `state_snapshot`, `policy_version`; not `decision-receipt.schema.json`.

Bringing it "under the same contract version and schemas" (ideation assumption 3) therefore means either adding a PAMA evaluation to the JS path or declaring that the JS surface implements only the recall-admission and correction-commit stages of the contract and says so in its conformance claim. The conformance harness (`reference/run_conformance.py`) claims level 0 for the Python reference today; the JS surface claims nothing.

## 6. Blueprint alignment

| Claim | Source | Finding | Status |
|---|---|---|---|
| PRD-001 requires four distinguishable stages | issue #362 | eight stages and ten operations (R1, lines 115-130) | **DRIFT** -- the issue understates the requirement |
| "no approval stage at all" | issue #362 | true at the boundary; internally the qualified-evidence discharge (ADR-037 4a) is the honest approval, with no public entry point | MATCH, with the route identified |
| Inputs unversioned, outputs versioned | issue #362 | confirmed; 46/58 outputs carry `schema_version` | MATCH |
| The JS runtime diverges in scope model, reason codes, receipt shape, and has idempotency Python lacks | issue #362 | confirmed and enumerated (section 5); it also has no PAMA | MATCH, sharper |
| Changing these types touches 55 importers | issue #362 | 65 files import the adapter today; option B touches none of them | **DRIFT** -- the count grew; the cost depends on shape |

## 7. Decisions for the operator, now with measurements

1. **Shape.** Option B (envelope) is recommended: it touches no existing importer, and it keeps the 27-field `Proposal` and the ADR-037 remnants out of the frozen contract. Option A freezes them.
2. **Approval.** The public approval entry point should be the qualified-evidence / attestation discharge of ADR-037 4a, exposed on the envelope as the `approve` stage; any other route is the assertion pattern 4b-2 removed. R1's `action authority` stage maps to `procedural_memory.apply_action_governance` and needs its own envelope form, which the ideation did not anticipate.
3. **JS runtime.** Two honest options: give it a PAMA evaluation (a real port of `policy.evaluate` and the receipt schema), or declare it a partial implementation of the contract's recall-admission and correction-commit stages with a conformance claim that says so. Adopting its shape for the reference (ideation option C) remains rejected.

## 8. Recommendation

Hold `/qor-plan` until the three decisions are taken. The plan then covers, in order: the envelope schemas (proposal, recall context, result) with a contract version tied to ADR-030's compatibility states; the eight-stage entry points on the envelope, with `approve` bound to ADR-037 4a and negative controls re-run through the public surface; a conformance claim per surface. #363 and #364 legs 2-3 follow the freeze.

## 9. Updated knowledge

Issue #362 cites PRD-001 for four stages; the PRD names eight and ten operations. Requirements cited from memory in an issue are re-read at research, not trusted.

---

_Research complete. Findings are advisory — implementation decisions remain with the Governor._
