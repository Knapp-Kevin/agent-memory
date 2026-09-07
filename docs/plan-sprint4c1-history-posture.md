# Plan: Sprint 4c-1 — `history` and `posture` on the public surface, contract `1.1.0`

**change_class**: feature
**doc_tier**: standard
**risk_grade**: L3
**research_artifact**: docs/research-brief-sprint4c-remaining-stages-2026-09-07.md (ledger Entry #48)
**iteration**: 2 (attempt-1 VETO V1-V3 and advisories A1-A6 amended; every record shape below was printed from the code, on the branches named, before being locked. Gate mapping: `plan-iter1..2.json` iteration 1; `plan-iter3..4.json` this iteration, the latter after two citations were rephrased; `plan-iter5.json` with the attempt-2 condition C1 and advisories applied)

**boundaries**:
- limitations: both entry points read; neither writes or evaluates. `history` returns what the adapter already retains for a target (its audit events, current fact, state version, tombstone status, and the rejected-value history of one value when a value is given); `posture` returns the doctor's report for a configuration. No new record is invented: the events are `memory-audit-event` records; the report is what `agent-memory doctor` prints, given a schema.
- non_goals: Sprint 4c-2 (action authority, execution evidence -- ideation first, brief section 2); Sprint 4b (held); #363 (the state directory the doctor inspects stays as it is); derivation chains (`derivation-evidence` has its own producers); any change to `doctor.diagnose`, `load_runtime_configuration`, the adapter's methods, or PAMA.
- exclusions: every existing schema except `api-result-envelope` (additive) and the three `api-*` `contract_version` constants; `schemas/` is not moved; no new dependency.

## Open Questions

None.

## Locked Decisions

**LD1 — Contract `1.1.0`, additive, and the compatibility rule corrected to mean it.** `contract.CONTRACT_VERSION` becomes `"1.1.0"`; the three envelope schemas accept `contract_version` in `{"1.0.0", "1.1.0"}` (enum) instead of the `1.0.0` const; the result envelope emits `1.1.0`. Sprint 4a's `compatibility()` returns `migration_required` for a *lower* minor of the same major (lines 45-56 of `api/contract.py`), which is inverted for additive versioning: an implementation at `1.1.0` understands every `1.0.0` envelope, while a `1.2.0` envelope may carry fields this implementation lacks. Corrected rule, ADR-030's four states kept: same major and envelope minor `<=` ours -> `current`; same major and envelope minor `>` ours -> `migration_required`; different major -> `incompatible`; absent or unparseable -> `unknown`. `test_api_contract.test_compatibility_states` is the one existing test edited: `1.0.0` and `1.1.0` -> `current`, `1.2.0` -> `migration_required`, `0.9.0` and `2.0.0` -> `incompatible`; its trailing block (lines 47-51) that asserted the inverted rule through the constant is deleted. The direction is this plan's reasoning about additive minors; ADR-030 supplies the four states and the rule that `unknown` is not current, not the direction. The correction travels with the feature because the `1.1.0` bump is the first moment the direction is observable.
Grep-evidence for `reference/agentmem_ref/api/contract.py:20`:
`git show origin/main:reference/agentmem_ref/api/contract.py | grep -nE '^CONTRACT_VERSION' -> 20:CONTRACT_VERSION = "1.0.0"`
Grep-evidence for `reference/agentmem_ref/api/contract.py:45`:
`git show origin/main:reference/agentmem_ref/api/contract.py | grep -nE '^def compatibility' -> 45:def compatibility(envelope: Mapping[str, Any]) -> str:`

**LD2 — `history(memory, target_envelope, *, fact_text=None)` returns retained records for one target.** A fourth schema, `schemas/api-target-envelope.schema.json` (`contract_version`, `target_reference`; `additionalProperties: false`), is the input. The result, `stage: "history"`, carries a `history` object: `current_fact_uuid` (`memory.current_fact_uuid`), `state_version` (`memory.state_version`), `tombstoned` (`target in memory.tombstoned_ids()`), `events` (every record in `memory.events` whose `memory_id` equals the target: the commit and deletion events the adapter builds with `_event` at line 823 and appends at line 344. Recall events, appended at line 499 and built by `_recall_event` at lines 556-609, deliberately carry **no** `memory_id` -- "a recall event legitimately spans many candidates" -- and are therefore **not** part of a target's history; a consumer reads them from `memory.events` directly. Observed: after one commit and one recall, the commit's `memory.propose`, `memory.authorize`, `memory.commit` and `memory.receipt` events (and `memory.readmission_blocked` when a commit is blocked; `memory.delete` on deletion) carry the target and the recall's `memory.recall` event has none), and `rejected_values` (`memory.rejected_value_history(target, fact_text)` when `fact_text` is given, else omitted -- the registry is keyed by value, lines 226-227 of `core/readmission.py`, and this plan adds no per-memory listing to core). An unknown target returns `current_fact_uuid: null`, `state_version: 0`, empty `events`; it is not a refusal.
Grep-evidence for `reference/agentmem_ref/runtime/adapter.py:161`:
`git show origin/main:reference/agentmem_ref/runtime/adapter.py | grep -nE '^        self\.events: list\[dict\] = \[\]' -> 161:        self.events: list[dict] = []`
Grep-evidence for `reference/agentmem_ref/runtime/adapter.py:673`:
`git show origin/main:reference/agentmem_ref/runtime/adapter.py | grep -nE '^    def rejected_value_history' -> 673:    def rejected_value_history(self, memory_id: str, fact_text: str) -> tuple[dict, ...]:`
Grep-evidence for `reference/agentmem_ref/runtime/adapter.py:676`:
`git show origin/main:reference/agentmem_ref/runtime/adapter.py | grep -nE '^    def tombstoned_ids' -> 676:    def tombstoned_ids(self) -> set[str]:`

**LD3 — `posture(config_path, *, qualification_path=None, state_dir=None)` returns the doctor's report under a schema.** It calls `doctor.diagnose(config_path, qualification_path=..., state_dir=...)` unchanged and returns `stage: "posture"` with `posture` = the report. `schemas/api-posture-report.schema.json` (new) declares the report as `diagnose` produces it, printed on the composed fixture (`reference/fixtures/runtime-configuration/reference-composed-runtime.json`, the fixture `test_cli_doctor.py` already drives) with and without a `state_dir`. Top-level keys, all required: `schema_version`, `command`, `configuration` (`status`, `digest`, `entry_mode`, `profile_id`, `profile_version`, `route_count`, `required_projection_ids`, `authority_effect`), `qualification` (`status`, `binding_count`, `scope`), `durable_state`, `recovery`, `currentness`, `provider_availability` (each with `status`), `configuration_startable` (boolean), `operational_readiness`, `authority_effect`. The top level is open (`additionalProperties: true`) and so are the `durable_state`, `recovery`, `currentness` and `provider_availability` sub-objects, whose keys vary by branch (lines 272-309 of `doctor.py`: `state_dir` / `configuration_binding_present`, `detail` or the recovery evidence keys); each requires only `status`. Only `configuration` and `qualification`, whose shape does not vary, are closed. The test drives both the no-`state_dir` branch and an empty `state_dir`. `posture` takes paths, not an adapter: posture is a property of a configuration, not of a memory, so it has no input envelope and emits `compatibility: current` (the implementation's own version). A missing or invalid configuration (`DiagnosticInputError`, lines 48-58 of `doctor.py`, a `ValueError`) surfaces as `stage: "none"` with `validation_error` naming it; nothing is raised through the surface.
Grep-evidence for `reference/agentmem_ref/runtime/doctor.py:206`:
`git show origin/main:reference/agentmem_ref/runtime/doctor.py | grep -nE '^def diagnose' -> 206:def diagnose(`
Grep-evidence for `reference/tests/test_cli_doctor.py:20`:
`git show origin/main:reference/tests/test_cli_doctor.py | grep -nE '^COMPOSED' -> 20:COMPOSED = FIXTURES / "reference-composed-runtime.json"`

**LD4 — The result envelope grows additively.** `schemas/api-result-envelope.schema.json`: `stage` enum adds `history` and `posture`; properties add `history` (object, `additionalProperties: false`, the five fields of LD2, with `required` excluding `rejected_values` since it is present only when a value is given) and `posture` (`$ref`-free: an object validated separately against `api-posture-report`); nothing existing changes. `contract.result()` keeps validating every result before it is returned, so a `history` result with a stray key fails at the surface, not at the consumer.
Grep-evidence for `schemas/api-result-envelope.schema.json:3`:
`git show origin/main:schemas/api-result-envelope.schema.json | grep -nE '"\$id"' -> 3:  "$id": "https://github.com/MythologIQ-Labs-LLC/agent-memory/schemas/api-result-envelope.schema.json",`

**LD5 — DoD 20 stays asserted.** `test_api_dod20.py` classifies every function in `surface.__all__`; `history` and `posture` join the readers. `test_readers_reach_no_mutation_seam` calls each reader explicitly -- `history` against the recording adapter (no call seen) and `posture` against the composed fixture -- and `posture`'s read-only property is structural: it takes no adapter, which the test states by asserting its signature has no `memory` parameter (`inspect.signature`).

**LD6 — Documentation.** `docs/44-public-api-contract.md`: version `1.1.0`, the corrected compatibility table (with the 4a inversion named), the two new rows in the stages table, the target envelope, and the 4c split (4c-2 deferred to ideation with the reason). `reference/README.md` paragraph updated. FEATURE_INDEX: FX026 new; FX024 modified (version, compatibility rule).

## Phase 1: schemas, version, compatibility

### Affected Files

- `reference/tests/test_api_contract.py` — `test_compatibility_states` re-stated per LD1 (the one existing-test edit); new `test_target_envelope_validates`.
- `schemas/api-target-envelope.schema.json`, `schemas/api-posture-report.schema.json` — new.
- `schemas/api-proposal-envelope.schema.json`, `api-recall-context.schema.json`, `api-result-envelope.schema.json` — `contract_version` enum; result envelope additions (LD4).
- `reference/fixtures/api/target-envelope.example.json` — new.
- `reference/agentmem_ref/api/contract.py` — `CONTRACT_VERSION`, `compatibility`, `TARGET_SCHEMA`, `POSTURE_SCHEMA`, `validate_target_envelope`.

### Unit Tests

- `test_compatibility_states` — `1.0.0` current, `1.1.0` current, `1.2.0` migration_required, `0.9.0` incompatible, `2.0.0` incompatible, absent unknown, malformed unknown. Red on `origin/main` for `1.2.0` (today `current`) and `1.0.0` would be red once `CONTRACT_VERSION` moves (today `current` only because it equals the constant).
- `test_target_envelope_validates` — the example validates; an extra key is rejected; `1.0.0` and `1.1.0` both accepted.
- `test_result_envelope_validates_against_its_schema` (existing, unchanged) keeps passing with the additive schema.

## Phase 2: the two entry points

### Affected Files

- `reference/tests/test_api_history_posture.py` — new.
- `reference/tests/test_api_dod20.py` — `READERS` gains `history` and `posture` (the meta-test's classification; an existing-test edit declared here).
- `reference/agentmem_ref/api/surface.py` — `history`, `posture`; `__all__`.

### Unit Tests

- `test_history_after_commit_and_recall` — commit a promotion for two targets, recall: `history` for the first returns its current fact uuid, `state_version == 1`, `tombstoned is False`, `events` all carrying that target's `memory_id` and including `memory.propose`, and none of the second target's; the recall event is absent from both (it carries no `memory_id`); unknown target -> `current_fact_uuid` null, `state_version` 0, empty `events`, `stage == "history"`.
- `test_history_rejected_values_by_value` (audit C1) — a parked correction records nothing: `history` with its value returns an empty `rejected_values`; then a correction committed with qualified evidence supersedes the prior value: `history` with the **superseded** value returns exactly one record whose `superseded_fact_uuid` equals the fact that was current before, and `state_version == 2`. The registry is written only by the commit path (`adapter.py:294-296, 400`).
- `test_history_after_forget` — after a governed deletion that commits, `tombstoned is True` and `current_fact_uuid is None`.
- `test_posture_on_the_composed_fixture` — `posture(COMPOSED, state_dir=<empty temp dir>)` and `posture(COMPOSED)` each return `stage == "posture"`, `compatibility == "current"`, and a report validating against `api-posture-report` with `operational_readiness` and `configuration_startable` present; `posture(<nonexistent path>)` returns `stage == "none"` with `validation_error` containing "not found".
- `test_api_dod20` (existing, extended) — readers include `history`, `posture`; no seam reached.
- Adversarial (recorded in the seal): `history` given an event of another target (filter removed) fails the isolation assertion; `compatibility` reverted to 4a's rule fails `test_compatibility_states`; the posture schema edited to require a key the report lacks fails the posture test.

## Phase 3: documentation and packaging proof

### Affected Files

- `docs/44-public-api-contract.md`, `reference/README.md` — LD6.
- `docs/FEATURE_INDEX.md` (FX026 new, FX024 modified), `docs/SYSTEM_STATE.md`, `docs/GOVERNANCE_INDEX.md`.
- `.github/workflows/cli-doctor.yml` — the `wheel-install` step's inline envelope already uses `contract.CONTRACT_VERSION`, so it follows the bump; the step additionally asserts `surface.__all__` contains `history` and `posture` and validates a target envelope against the packaged `api-target-envelope` schema. (`posture` is not exercised from the wheel: the composed fixture is not packaged.)

### Unit Tests

- Local wheel smoke by the job's recipe from outside the checkout: exit 0; exit 1 when built without `api-target-envelope.schema.json` (the negative).

## Definition of Done

### Deliverable: history and posture at the boundary

- **D1**: a consumer can inspect a target's retained history and a configuration's posture through the same surface and result envelope as the six stages, under contract `1.1.0`.
- **D2**: `surface.history`, `surface.posture`; `api-target-envelope` and `api-posture-report` schemas; result envelope additions; `CONTRACT_VERSION "1.1.0"`.
- **D3**: ledger SESSION SEAL (#50 after audit #49, or later if attempts repeat); `docs/44`; FX026; SYSTEM_STATE; GOVERNANCE_INDEX rows.
- **D4**: the new tests pass; the two existing-test edits (`test_compatibility_states`, `test_api_dod20` readers) are the only edits; suite green at its run count; three adversarial mutations caught; wheel smoke exit 0 / exit 1.

### Deliverable: the compatibility rule follows additive versioning (the plan's reasoning; ADR-030 supplies the states)

- **D1**: an older minor of the same major is `current`; a newer minor is `migration_required`; the 4a inversion is corrected and named in the contract document.
- **D2**: `contract.compatibility` per LD1.
- **D3**: `docs/44` compatibility table.
- **D4**: `test_compatibility_states` per LD1; the adversarial revert fails it.

## Feature Inventory Touches

| entry_id | operation | test_path | test_descriptor |
|---|---|---|---|
| FX026 (FX025 is reserved by the held Sprint 4b plan) | NEW | `reference/tests/test_api_history_posture.py` | `history` returns a target's retained audit events, current fact, state version, tombstone status and (given a value) rejected-value history, isolated per target; `posture` returns the doctor's report under `api-posture-report`; both read only (DoD-20 meta-test) |
| FX024 | MODIFIED | `reference/tests/test_api_contract.py` | contract `1.1.0`; compatibility: older minor `current`, newer minor `migration_required` |

## CI Commands

- `python -m unittest reference.tests.test_api_contract reference.tests.test_api_history_posture reference.tests.test_api_dod20` — the touched tests.
- `python -m unittest discover -s reference/tests -t reference` — full suite; the count is read from the run.
- `python scripts/validate_schemas.py` and `python scripts/validate_fixtures.py fixtures` — schemas and fixtures.
- `python -m build --outdir <scratch>/dist4c <repo>` then install into a fresh venv and run the `wheel-install` step from outside the checkout (Windows: `<scratch>/wheelvenv/Scripts/python.exe`; the wheel named explicitly).
- `python scripts/validate_markdown_links.py docs/44-public-api-contract.md reference/README.md docs/FEATURE_INDEX.md` — documentation links.
- `python scripts/verify_seals.py` — anchors match.
