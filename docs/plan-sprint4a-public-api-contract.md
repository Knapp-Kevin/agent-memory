# Plan: Sprint 4a — the public contract: envelopes, a version, and six stages at the boundary

**change_class**: feature
**doc_tier**: system
**risk_grade**: L3
**research_artifact**: docs/research-brief-sprint4-public-api-2026-09-06.md (ledger Entry #42); ideation `.qor/gates/2026-09-06T2140-f7a9c3/ideation-iter2.json` (operator decisions 2026-09-06: envelope shape; approval bound to ADR-037 4a; JS runtime gets a PAMA port)
**iteration**: 2 (attempt-1 VETO V1-V4 and advisories A1-A5 amended. Gate mapping: `plan-iter1..3.json` were written for iteration 1 before attempt 1; `plan-iter4..6.json` were rewritten during the iteration-2 amendment as lint findings were closed; `plan-iter7.json` is this iteration with the attempt-2 advisories applied)

**terms_introduced**:
- term: proposal envelope
  home: docs/44-public-api-contract.md
- term: recall context envelope
  home: docs/44-public-api-contract.md
- term: result envelope
  home: docs/44-public-api-contract.md
- term: contract version
  home: docs/44-public-api-contract.md

**boundaries**:
- limitations: the contract wraps `GovernedMemoryAdapter`; the adapter's own methods and the 65 files that import it are untouched and remain valid. Six of PRD-001 R1's eight stages get boundary forms here (proposal, decision, approval, commit, retrieval candidate, recall admission); action authority and execution evidence are Sprint 4c, with their own envelopes; the JS PAMA port is Sprint 4b. One contract version, `1.0.0`.
- non_goals: Sprint 4b (JS runtime PAMA port and receipt schema); Sprint 4c (action authority, execution evidence, history/provenance and posture inspection entry points); #363; #364 legs 2-3; #392; removing the flat-path aliases; any change to PAMA's decision table, to `evaluate_with_qualified_evidence`, or to `_apply_review`.
- exclusions: every existing schema and fixture; `schemas/` is not moved; no new discharge route for `require_review`; no caller-supplied verifier registry anywhere on the public surface.

## Open Questions

None. The three contract decisions were taken by the operator on 2026-09-06 and are recorded on the ideation gate.

## Locked Decisions

**LD1 — Three schemas define the public inputs and output, each carrying `contract_version`.** `schemas/api-proposal-envelope.schema.json` (the public form of a proposal: exactly the `Proposal` fields except the four evaluator-side ones. Frozen set: `proposal_id`, `actor_id`, `charter_version`, `target_reference`, `target_class`, `scope`, `operation`, `current_strength`, `proposed_strength`, `downstream_authority`, `reversibility`, `risk_class`, `evidence_refs`, `estimator_refs`, `estimator_versions`, `confidence`, `requested_scope_change`, `state_snapshot`, `tenant_ref`, `purpose`, `isolation_domain_refs`, `required_isolation_domain_refs`, `project_ref`, `task_ref` -- 24 fields, lines 124-151 of `core/policy.py`. Excluded and rejected by `additionalProperties: false`: `review_satisfied`, `approval_refs`, `approves_own_authority`, `actor_authority_resolved`); `schemas/api-recall-context.schema.json` (the `RecallContext` fields); `schemas/api-result-envelope.schema.json` (`contract_version`, `stage`, `compatibility`, `outcome`, `decision` projection, optional `receipt`, optional `refusal`, optional `candidates` / `admissions`). All three carry `$id` in the repository's pattern and `contract_version` as `const "1.0.0"`. `scripts/validate_schemas.py` checks every schema under `schemas/` (`:29-33`) so they are covered by the existing validator.
Grep-evidence for `reference/agentmem_ref/core/policy.py:121`:
`git show origin/main:reference/agentmem_ref/core/policy.py | grep -nE '^class Proposal' -> 121:class Proposal:`
Grep-evidence for `reference/agentmem_ref/runtime/adapter.py:102`:
`git show origin/main:reference/agentmem_ref/runtime/adapter.py | grep -nE '^class RecallContext' -> 102:class RecallContext:`

**LD2 — A new `api` layer, between `memory` and `crg`, holds the contract.** `scripts/restructure_package.py` gains `"api"` in `LAYER_ORDER` after `"memory"`, a `LAYER_DOCS["api"]` docstring (the mover's `move()` reads it at lines 145-146 of `restructure_package.py`; `--check` does not, but the mover must stay runnable), and a `LAYERS["api"]` entry of two modules: `contract` (version constant, envelope validation through `receipts.validate`, envelope-to-dataclass and decision-to-projection conversion, the ADR-030 compatibility evaluation) and `surface` (the stage entry points). The layout test reads the order from the mover, so the new layer is enforced the moment it is declared; the layer may import `runtime` and `memory` and nothing above it. The mover's alias rule applies: `agentmem_ref/contract.py` and `agentmem_ref/surface.py` are `sys.modules` aliases, so `problems()` stays empty. `__init__` gains `from .api import surface` and `"surface"` in `__all__`.
Grep-evidence for `scripts/restructure_package.py:35`:
`git show origin/main:scripts/restructure_package.py | grep -nE '^LAYER_ORDER' -> 35:LAYER_ORDER = ("core", "state", "contracts", "runtime", "memory", "crg", "harness")`
Grep-evidence for `reference/agentmem_ref/__init__.py:13`:
`git show origin/main:reference/agentmem_ref/__init__.py | grep -nE '^__all__' -> 13:__all__ = ["adapter", "governance_projection", "policy", "receipts", "substrate"]`

**LD3 — Compatibility is ADR-030's four states, evaluated before any stage runs.** `contract.compatibility(envelope)` returns `current` when `contract_version == "1.0.0"`, `migration_required` when the major matches and the minor is lower, `incompatible` when the major differs, `unknown` when the field is absent or unparseable; every surface function returns a result envelope with that state and runs the stage only on `current`. "Serialization success is not semantic compatibility": schema validation and compatibility are two checks, both recorded.
Grep-evidence for `docs/adr/ADR-030-temporal-policy-consumers-require-versioned-compatible-projections.md:19`:
`git show origin/main:docs/adr/ADR-030-temporal-policy-consumers-require-versioned-compatible-projections.md | grep -nE '^Serialization success' -> 19:Serialization success is not semantic compatibility.`

**LD4 — Five functions covering six stages, each a function of the adapter and an envelope.** In `api/surface.py`: `propose(memory, envelope)` validates, converts, evaluates `policy.evaluate` and returns the decision projection with `stage: "proposal"`; nothing is written. `decide` is the projection inside every result (the `decision` stage has a boundary form already: `pama-decision`). `approve(memory, envelope, *, evidence=(), attestation=None)` evaluates through the adapter's evaluator-owned registry (LD5) and returns the decision with `discharge_authority`; nothing is written. `commit(memory, envelope, fact_text, *, evidence=(), attestation=None)` calls `memory.commit_proposal(proposal, fact_text, evidence=..., attestation=...)` and returns `stage: "commit"` with the receipt. `recall(memory, query, context_envelope)` calls `governed_recall` and returns `stage: "recall"` with `candidates` (the retrieval-candidate stage) and `admissions` (the recall-admission stage: the adapter's per-candidate decision records, each carrying `outcome` (`admit` | `block`) and `reason_code`, lines 490-528 of `adapter.py`, passed through unchanged). `forget(memory, envelope, *, evidence=(), attestation=None)` resolves the target's current fact (`memory.current_fact_uuid`, empty when absent so the adapter refuses `fact_not_found`) and calls `governed_delete(proposal, fact_uuid, evidence=evidence, external_verification=attestation)` -- that method's keyword is `external_verification` (line 686 of `adapter.py`). Every function is under 40 lines.
Grep-evidence for `reference/agentmem_ref/runtime/adapter.py:178`:
`git show origin/main:reference/agentmem_ref/runtime/adapter.py | grep -nE '^    def commit_proposal' -> 178:    def commit_proposal(`
Grep-evidence for `reference/agentmem_ref/runtime/adapter.py:444`:
`git show origin/main:reference/agentmem_ref/runtime/adapter.py | grep -nE '^    def governed_recall' -> 444:    def governed_recall(self, query: str, context: RecallContext | None = None) -> AdmissionResult:`
Grep-evidence for `reference/agentmem_ref/runtime/adapter.py:681`:
`git show origin/main:reference/agentmem_ref/runtime/adapter.py | grep -nE '^    def governed_delete' -> 681:    def governed_delete(`

**LD5 — Approval is the ADR-037 4a discharge, through a registry the adapter owns; the surface never accepts verifiers.** `GovernedMemoryAdapter` gains one public method, `evaluate_proposal(proposal, *, evidence=(), attestation=None) -> Decision`, which runs `policy.evaluate_with_qualified_evidence(proposal, group_by_dependence(evidence, verifiers=self._verifier_registry.as_mapping()), attestation=attestation)` when evidence is present, `policy.evaluate_with_external_verification(proposal, attestation)` when only an attestation is, and `policy.evaluate` otherwise -- the three-way selection `governed_delete` makes today (lines 706-723 of `adapter.py`). `commit_proposal` is **not** refactored: its selection is two-way (lines 220-231 of `adapter.py`; an attestation without evidence is ignored there), and changing it is a behaviour change outside this plan. The asymmetry is recorded in `docs/44-public-api-contract.md` ("What `commit` forwards and what the adapter does with it") and raised as a follow-up issue at handoff; the surface's `commit` forwards both arguments unchanged, and `test_commit_attestation_only_is_ignored_by_the_adapter_today` pins the current behaviour so the follow-up has a red test to turn green. No `verifiers=` parameter exists on any surface function; the envelope schema rejects `review_satisfied` and `approval_refs`; a negative test proves an envelope carrying either is refused at validation and that `approve` with no evidence at medium risk returns `require_review` with an empty `discharge_authority` and `enter_pending_verification` among its permitted actions (**addendum at implementation**: the base evaluation carries no reason string; `review_requires_qualified_evidence` belongs to the legacy asserted route).
Grep-evidence for `reference/agentmem_ref/core/policy.py:447`:
`git show origin/main:reference/agentmem_ref/core/policy.py | grep -nE '^def evaluate_with_qualified_evidence' -> 447:def evaluate_with_qualified_evidence(`
Grep-evidence for `reference/agentmem_ref/core/policy.py:407`:
`git show origin/main:reference/agentmem_ref/core/policy.py | grep -nE '^def evaluate_with_external_verification' -> 407:def evaluate_with_external_verification(`

**LD6 — DoD 20 is asserted at the public surface, not narrated.** A meta-test enumerates every public function in `api/surface.py` and, for each that can reach `commit_proposal` or `governed_delete`, drives it through a recording adapter: with evidence supplied, the recorder sees the same evidence forwarded; with none, at medium risk, the adapter parks (`committed=False`, decision `require_review`). `propose`, `approve` and `recall` are shown to call neither.

**LD7 — The contract is documented once, at its home.** `docs/44-public-api-contract.md` (new; `doc_tier: system` term home): the three envelopes, the version and compatibility states, the six stages and what each returns, what the surface refuses and why (the forbidden interpretations from the ideation record), and the two stages deferred to 4c. `reference/README.md` gains one paragraph pointing there; `docs/34-adapter-contracts.md` is unchanged (it documents adapter seams, not the consumer contract).

## Phase 1: schemas and the contract module

### Affected Files

- `reference/tests/test_api_contract.py` — new. Envelope validation (valid; each forbidden field rejected; missing `contract_version` rejected); compatibility states for `1.0.0`, `1.1.0`, `0.9.0`, `2.0.0`, absent, malformed; envelope-to-`Proposal` conversion round-trips every public field and sets the evaluator-side fields to their defaults; decision projection carries `outcome`, `permitted_actions`, `prohibited_actions`, `reasons`, `policy_version`, `discharge_authority`.
- `schemas/api-proposal-envelope.schema.json`, `schemas/api-recall-context.schema.json`, `schemas/api-result-envelope.schema.json` — new (LD1).
- `reference/fixtures/api/proposal-envelope.example.json`, `recall-context.example.json` — new; the documents the tests validate.
- `scripts/restructure_package.py` — `api` layer (LD2).
- `reference/agentmem_ref/api/__init__.py`, `reference/agentmem_ref/api/contract.py` — new (LD2, LD3).
- `reference/agentmem_ref/contract.py` — alias (mover rule).

### Unit Tests

- `test_envelope_validates_and_forbidden_fields_are_rejected` — `contract.validate_proposal_envelope(example)` returns the document; adding `review_satisfied`, `approval_refs`, `approves_own_authority`, or `actor_authority_resolved` raises `ValueError` naming the property.
- `test_compatibility_states` — six inputs, the ADR-030 state for each.
- `test_envelope_to_proposal_round_trip` — every public field equals the `Proposal` field; `review_satisfied is False`, `approval_refs == ()`, `approves_own_authority is False`.
- `test_decision_projection_fields` — projection of a `policy.evaluate` result at medium correction has `outcome == "require_review"`, `reasons == []` (the base evaluation records no discharge reason because nothing was claimed; `review_requires_qualified_evidence` is emitted only on the legacy asserted route, which the envelope cannot express -- **addendum at implementation**, observed), and `permitted_actions` containing `enter_pending_verification`.
- `test_package_layout` (existing) — its `__all__` assertion is updated to include `"surface"` (the one existing-test edit in this plan); order, aliases and no-later-layer-import pass with the new layer read from the mover.

## Phase 2: the surface and the adapter's evaluation method

### Affected Files

- `reference/tests/test_api_surface.py` — new; per LD4 and LD5.
- `reference/tests/test_api_dod20.py` — new; the LD6 meta-test.
- `reference/agentmem_ref/runtime/adapter.py` — `evaluate_proposal` (LD5), a new method with `governed_delete`'s three-way selection; `commit_proposal` and `governed_delete` are untouched (the existing suite, at its current count, is the guard).
- `reference/agentmem_ref/api/surface.py` — new (LD4); `reference/agentmem_ref/surface.py` alias.
- `reference/agentmem_ref/__init__.py` — export.

### Unit Tests

- `test_propose_evaluates_without_writing` — medium correction: `outcome == "require_review"`, `stage == "proposal"`, `memory.state_version(target)` unchanged, recorder saw no `commit_proposal`.
- `test_approve_with_asserted_evidence_discharges_at_medium` — an `artifact_bound` item from the procedural-memory producer (an existing producer, not a minted one): `outcome == "allow_with_ledger"`, `discharge_authority == "delegated_policy"`, nothing written.
- `test_approve_with_attestation_discharges_external_verification_at_critical` — `ExternalVerification` with `human_confirmation`: outcome allows; nothing written.
- `test_approve_without_evidence_parks` — `require_review`, `discharge_authority == ""`, `enter_pending_verification` permitted.
- `test_commit_forwards_evidence_and_parks_without` — recorder sees the evidence object; without it, `committed is False`, decision `require_review`.
- `test_recall_returns_candidates_and_admissions` — after a committed promotion, `candidates` contains the fact id and `admissions[fact_id]["outcome"] == "admit"` with `reason_code == "builtin_admission"`; with a scope the context does not cover, `admissions[fact_id]["outcome"] == "block"` and `reason_code` names the refusal.
- `test_commit_attestation_only_is_ignored_by_the_adapter_today` — `commit` of a `correction` at `critical` (the row is `require_external_verification`) with an attestation and no evidence: the adapter's outcome is `require_external_verification` (the two-way selection ignores the attestation); pins the recorded asymmetry.
- `test_forget_forwards_and_refuses_unknown` — `governed_delete` refusal surfaces as `refusal`; with evidence, forwarded.
- `test_incompatible_version_runs_no_stage` — `contract_version: "2.0.0"` returns `compatibility == "incompatible"`, `stage` unchanged, recorder saw nothing.
- `test_api_dod20` — LD6 meta-test over `surface.__all__`.
- Adversarial (recorded in the seal): a surface function edited to drop `evidence=` fails the DoD-20 test; an envelope schema edited to allow `review_satisfied` fails the forbidden-fields test; `api/surface.py` importing `..crg` fails the layout test.

## Phase 3: documentation and packaging proof

### Affected Files

- `docs/44-public-api-contract.md` — new (LD7).
- `reference/README.md` — one paragraph.
- `docs/FEATURE_INDEX.md` (FX024), `docs/SYSTEM_STATE.md`, `docs/GOVERNANCE_INDEX.md`, `docs/ARCHITECTURE_PLAN.md` file tree (the `api/` layer).
- `.github/workflows/cli-doctor.yml` — the `wheel-install` "Installed runtime modules resolve their schemas" step also imports `agentmem_ref.api.surface` and validates the proposal example against the packaged `api-proposal-envelope` schema from outside the checkout, so the new schemas are proven to ship.

### Unit Tests

- `python scripts/validate_markdown_links.py` over the new and changed docs; `python scripts/validate_doctrine_boundaries.py` unchanged surface; the wheel smoke run locally by the job's recipe (exit 0; and exit 1 on a wheel built without the three schemas, by temporarily excluding them, as the negative).

## Definition of Done

### Deliverable: the contract

- **D1**: a consumer can express a proposal and a recall context in schema-backed, versioned envelopes, and every result names its contract version, compatibility state, stage and decision; PRD-001 R1's proposal, decision, approval, commit, retrieval-candidate and recall-admission stages are distinguishable at the boundary.
- **D2**: three schemas under `schemas/`; `agentmem_ref/api/{contract,surface}.py` with the functions named in LD3-LD4; `GovernedMemoryAdapter.evaluate_proposal`; `__init__` exports `surface`; mover `LAYER_ORDER` has `api` after `memory`.
- **D3**: ledger SESSION SEAL (#45; audit VETO #43, audit PASS #44); `docs/44-public-api-contract.md`; FX024; SYSTEM_STATE; GOVERNANCE_INDEX rows for plan and brief; ARCHITECTURE_PLAN tree; ideation gate cited.
- **D4**: all new tests pass; the existing suite passes at its current count (cited from the run at seal, not from SYSTEM_STATE); the only existing test edited is `test_package_layout.py`, whose `__all__` assertion gains `"surface"` and whose layer expectations come from the mover (FX022 MODIFIED); `test_package_layout` passes with the new layer; the three adversarial mutations fail their tests; the wheel smoke resolves the new schemas from outside the checkout and fails without them.

### Deliverable: approval is the honest discharge

- **D1**: the public `approve` stage discharges `require_review` only through qualified evidence or an attestation evaluated by the adapter's own registry; no public path accepts a verifier or an approval flag.
- **D2**: `evaluate_proposal` on the adapter; no `verifiers=` parameter on any surface function; envelope schemas reject the four evaluator-side fields.
- **D3**: `docs/44-public-api-contract.md` "What the surface refuses" and "What `commit` forwards and what the adapter does with it".
- **D4**: `test_approve_without_evidence_parks`, `test_envelope_validates_and_forbidden_fields_are_rejected`, `test_api_dod20`.

## Feature Inventory Touches

| entry_id | operation | test_path | test_descriptor |
|---|---|---|---|
| FX024 | NEW | `reference/tests/test_api_surface.py` | `propose`/`approve`/`commit`/`recall`/`forget` on versioned envelopes return result envelopes with ADR-030 compatibility, stage and decision; `approve` discharges only through the adapter's evaluator-owned registry; `commit`/`forget` forward evidence or park (DoD-20 meta-test in `test_api_dod20.py`) |
| FX022 | MODIFIED | `reference/tests/test_package_layout.py` | the layer order includes `api` between `memory` and `crg`; aliases for `contract` and `surface` are identical objects; `__all__` gains `"surface"` (the row's "exports unchanged" note is superseded) |
| FX001 | MODIFIED | `.github/workflows/cli-doctor.yml` (`wheel-install`) | the installed wheel imports `agentmem_ref.api.surface` and validates the proposal example against the packaged envelope schema |

## CI Commands

- `python -m unittest reference.tests.test_api_contract reference.tests.test_api_surface reference.tests.test_api_dod20` — the new tests.
- `python -m unittest discover -s reference/tests -t reference` — full suite; the count is read from the run.
- `python scripts/restructure_package.py --check` — layout with the `api` layer.
- `python scripts/validate_schemas.py` and `python scripts/validate_fixtures.py fixtures` — schemas and fixtures.
- `python -m build --outdir <scratch>/dist4a <repo>` then install into a fresh venv and run the extended `wheel-install` step script from outside the checkout (Windows: `<scratch>/wheelvenv/Scripts/python.exe`; the wheel named explicitly) — packaging proof and its negative.
- `python scripts/validate_markdown_links.py docs/44-public-api-contract.md reference/README.md docs/FEATURE_INDEX.md` — documentation links.
- `python scripts/verify_seals.py` — anchors match.
