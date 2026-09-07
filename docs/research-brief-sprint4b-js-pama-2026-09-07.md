# Research Brief: Sprint 4b — a PAMA evaluation for the JS runtime, measured before it is ported

**Date**: 2026-09-07
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 21.
**Implements**: the operator's 2026-09-06 decision ("port a PAMA eval") for issue #362's second surface, after Sprint 4a (Entry #45) froze the Python contract at `1.0.0`
**Scope**: what the JS runtime is today, what a faithful port of the Python PAMA evaluation consists of, what the receipt must become, and what the port must not do

## 1. The JS runtime, measured

`integrations/agent-memory-runtime/src/index.mjs` (354 lines) exports `CONTRACT_VERSION = '0.1'`, `ADAPTER_VERSION = '0.1.1'`, `MemoryAdapterError`, and `createGovernedMemoryAdapter({storage, clock, memoryIdFactory, eventIdFactory})` returning two frozen async functions:

- `recall(request)` (`:256-284`): normalizes `{scope, purpose, policy_version}`, loads a snapshot, admits records by exact scope and state (`admissionForRecord`, `:100-124`: `invalid_record`, `missing_identity`, `unknown_scope`, `out_of_scope`, `disputed`, `superseded`, `state_<x>`).
- `correct(request)` (`:286-353`): normalizes `{scope, memory_id, idempotency_key, policy_version, evidence_refs (min 1), authority_refs (min 1), replacement{kind, value_ref}}`; replays a prior receipt by `idempotency_key`; refuses if the target is not current; commits a replacement record plus a `correction_committed` event with `expected_revision` optimistic concurrency; returns `correctionReceipt` (`:194-…`).

There is **no policy evaluation anywhere in the file**: no operation, risk class, target class, downstream authority, reversibility; no outcome; no permitted or prohibited actions. Authority is `authority_refs.length >= 1`. The harness is `node --test test/*.test.mjs` (8 tests, 321 lines) under `.github/workflows/agent-memory-runtime-adapter.yml`, path-triggered on `integrations/agent-memory-runtime/**`, Node 22. Node 22.22 is available locally.

## 2. What a faithful port consists of

The Python evaluation (`reference/agentmem_ref/core/policy.py`) is small and closed:

| Piece | Lines | Content |
|---|---|---|
| base table | `:53-112` | 56 `(operation, risk_class)` cells over 14 operations and 4 risk classes; default `require_review` for an unknown cell (`_base_outcome`, `:207-208`) |
| floors | `:114-115`, `:211-222` | target class `M4`/`M5` -> at least `require_review`; downstream authority `A4` -> `require_review`, `A5` -> `require_external_verification` |
| modifiers | `:224-262` | `M-AUTH` (actor authority unresolved -> `block`); invariant 4 (self-approval -> `block`); required isolation domains not bound -> `block`; `M-SCOPE` (domain-schema mutation requesting scope expansion escalates to the scope-expansion cell); `M-IRREV` (irreversible -> at least `require_review`, high/critical -> at least `require_external_verification`); `M-EVID` (no evidence refs -> at least `require_review`) |
| strictness order | `:30-36` | `allow < allow_with_ledger < require_review < require_external_verification < block` |
| envelope | `:298-308` | permitted / prohibited actions per outcome (`enter_pending_verification`, `request_external_verification`, `collect_more_evidence`, `defer`) |
| discharge | `:407-560` | attestation (`evaluate_with_external_verification`) and qualified evidence (`evaluate_with_qualified_evidence`); **not** in scope for the port -- see section 4 |

The output the port must produce is the `pama-decision` record (`schemas/pama-decision.schema.json`: `proposal_id`, `proposing_actor{id, charter_version}`, `target{reference, class, scope}`, `mutation{operation, current_strength, proposed_strength, downstream_authority, reversibility, risk_class}`, `basis`, `policy`, `decision{outcome, permitted_actions, prohibited_actions}`) and the `decision-receipt` record (`receipt_id`, `requested_action`, `policy_version`, `permitted_actions`, `selected_action`, `selection_mode`, `timestamp`). Both schemas already exist and are what the Python reference emits through `receipts.build_pama_decision` / `build_receipt` (`core/receipts.py:140-230`).

## 3. What the port must not do

- **Not accept an asserted review.** `review_satisfied` + `approval_refs` is the route ADR-037 4b-2 removed; the JS `correct` request has `authority_refs` today, which is the same shape. The port evaluates the base table, floors and modifiers; `require_review` and `require_external_verification` **park** in JS exactly as in Python -- the correction is refused with the outcome and permitted actions, not committed.
- **Not invent a discharge.** Qualified evidence (`EvidenceItem`, verifier registries, `TransitionRuleCorpus`) and attestations are evaluator-held machinery on the Python side. Porting them is a later cycle, if ever; a JS port that ships them without the registry discipline would be the laundering pattern. Sprint 4b makes `correct` refuse honestly at `require_review` instead of committing on `authority_refs.length >= 1`.
- **Not fork the table.** The base table, floors, modifiers and strictness order are transcribed once, from `policy.py`, and a **cross-implementation conformance test** drives both evaluations over every `(operation, risk_class)` cell and every floor/modifier case from one JSON fixture (`reference/fixtures/api/pama-conformance.json`, generated from the Python side) and asserts identical outcomes and envelopes. The fixture is the contract between the two; the Python test regenerates and compares it, the JS test reads it.

## 4. What Sprint 4b changes, minimally

1. `integrations/agent-memory-runtime/src/policy.mjs` (new): `evaluate(proposal) -> {outcome, permitted_actions, prohibited_actions, reasons, policy_version}` -- the table, floors, modifiers, strictness and envelope; `policy_version` equals the Python `POLICY_VERSION` (`ref-p1`, `policy.py:21`).
2. `index.mjs`: `correct` builds a proposal from the request (`operation: 'correction'`, `risk_class` from the request -- a new required field -- `target_class`, `downstream_authority`, `reversibility` likewise required), calls `evaluate`, and **commits only on `allow` / `allow_with_ledger`**; otherwise returns a refusal carrying the decision. `recall` is unchanged. `CONTRACT_VERSION` becomes `'1.0.0'` **only if** the correction request adopts the proposal envelope's field names; that is a plan decision (section 6).
3. Receipts: the commit event gains the `pama-decision` record and the `decision-receipt` record (both schemas validated in the JS test against the canonical files read from `schemas/`); the existing `correction_committed` event keeps its fields.
4. Conformance fixture and its two consumers (Python regenerates and asserts; JS reads and asserts).
5. Existing eight JS tests: `correction requires explicit authority and evidence` becomes a park at `require_review` for the fixture's medium correction unless the request carries a risk class whose cell allows -- the test is re-stated against the table, not deleted.

## 5. Blueprint alignment

| Claim | Source | Finding | Status |
|---|---|---|---|
| The JS runtime "diverges in scope model, reason codes, and receipt shape" | issue #362 | confirmed, and it has no policy evaluation at all | MATCH, sharper |
| "port a PAMA eval" is a bounded transcription | operator decision | the evaluation is 56 cells, 2 floors, 6 modifiers, 1 order, 1 envelope -- bounded; discharge is not part of it | MATCH |
| "A bounded, host-neutral ESM adapter for governed runtime recall and correction/supersession" with "evidence and authority requirements for committed correction" | `integrations/agent-memory-runtime/README.md:3,14` | `correct` admits on record state and commits when `evidence_refs` and `authority_refs` each have at least one string; no decision table, floors, modifiers or outcome exist in the runtime | **DRIFT** -- "governed" overstates the runtime; the README is corrected in Sprint 4b |

## 6. Decisions for the plan

1. Whether the JS correction request adopts the Python proposal envelope's field names (so `CONTRACT_VERSION` can honestly say `1.0.0`) or keeps its own names with a mapping (then it stays `0.x` and declares partial conformance). The first is the honest reading of "under the same contract".
2. Whether `recall` also produces per-candidate `contextual-recall-admission` records (Python does) in this cycle or in 4c.

## 7. Recommendation

`/qor-plan` for Sprint 4b with the scope in section 4, the conformance fixture as the load-bearing test, and decision 1 taken as "adopt the envelope's names". L3: the JS runtime is a second public surface.

---

_Research complete. Findings are advisory — implementation decisions remain with the Governor._
