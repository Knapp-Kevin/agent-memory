# Plan: Sprint 3d — one schema resolver, and the `data-files` path retired (#365)

**change_class**: hotfix
**change_class_rationale**: a defect fix -- an installed wheel's schema lookup depends on a packaging path the wheel no longer needs -- with no new capability; L2 because it touches packaging and two runtime modules' lookups, not because it adds surface
**doc_tier**: standard
**risk_grade**: L2
**research_artifact**: docs/research-brief-sprint3d-packaging-remainder-2026-09-06.md (ledger Entry #37)
**iteration**: 3 (iteration 2 closed attempt-1 V1 and A1-A4 with red/green observed against `origin/main`; iteration 3 closes attempt-2 V2 -- the change-class rationale moved off the header line, header verified with `governance_helpers.parse_change_class` -- and A5-A6. Gate artifacts: `plan-iter3.json` is iteration 2, `plan-iter4.json` is this iteration)

**boundaries**:
- limitations: the two modules keep raising their own error types on a missing schema (`RuntimeConfigurationError`, `DiscoveryInputError`); only the lookup behind them changes. `schemas/` is not moved (#365's standing constraint).
- non_goals: #362 (public API), #364, #363; any change to `receipts.schema_dir()` itself, which Sprint 1 and Sprint 3a's audit C1 already proved; any change to `setup.py`'s build-time `_schemas/` copy.
- exclusions: every other module under `reference/agentmem_ref/`; every schema and fixture; every workflow other than `cli-doctor.yml`'s `wheel-install` job.

## Open Questions

None.

## Locked Decisions

**LD1 — Both modules resolve their schema through `receipts.schema_dir()`.** `runtime_config._configuration_schema_path()` returns `schema_dir() / "runtime-configuration.schema.json"` and `discovery._probe_schema_path()` returns `schema_dir() / "provider-probes.schema.json"`, each converting `FileNotFoundError` from `schema_dir()` (or a missing file under it) into the module's own error type with the same message shape as today. `runtime` may import `core` under the layer order (`core < state < contracts < runtime`); line 14 of `runtime/contextual_recall_adapter.py` already does.
Grep-evidence for `reference/agentmem_ref/core/receipts.py:37`:
`git show origin/main:reference/agentmem_ref/core/receipts.py | grep -nE '^def schema_dir' -> 37:def schema_dir() -> Path:`
Grep-evidence for `reference/agentmem_ref/runtime/runtime_config.py:234`:
`git show origin/main:reference/agentmem_ref/runtime/runtime_config.py | grep -nE 'metadata\.files' -> 234:        distribution_files = metadata.files(_DISTRIBUTION_NAME) or ()`
Grep-evidence for `reference/agentmem_ref/runtime/discovery.py:81`:
`git show origin/main:reference/agentmem_ref/runtime/discovery.py | grep -nE 'metadata\.files' -> 81:        distribution_files = metadata.files(_DISTRIBUTION_NAME) or ()`

**LD2 — The `data-files` machinery goes, entirely.** Removed: `from importlib import metadata` in `runtime_config.py` (line 17; line 11 of `discovery.py` keeps `util`, which line 179 uses, and drops `metadata`), `_DISTRIBUTION_NAME` and the two `_..._DATA_SUFFIX` constants, the two `_repo_root()` helpers and the `REPO_ROOT` imports they alone consumed (`runtime_config.py` lines 35 and 222-223; `discovery.py` lines 18 and 71-72), and `[tool.setuptools.data-files]` (`pyproject.toml` lines 37-41). `_schemas/*.json` (`pyproject.toml` lines 34-35) already carries both schemas.
Grep-evidence for `reference/agentmem_ref/runtime/runtime_config.py:40`:
`git show origin/main:reference/agentmem_ref/runtime/runtime_config.py | grep -nE '^_RUNTIME_SCHEMA_DATA_SUFFIX' -> 40:_RUNTIME_SCHEMA_DATA_SUFFIX = "agent_memory_reference/schemas/runtime-configuration.schema.json"`
Grep-evidence for `reference/agentmem_ref/runtime/discovery.py:23`:
`git show origin/main:reference/agentmem_ref/runtime/discovery.py | grep -nE '^_PROBE_SCHEMA_DATA_SUFFIX' -> 23:_PROBE_SCHEMA_DATA_SUFFIX = "agent_memory_reference/schemas/provider-probes.schema.json"`
Grep-evidence for `pyproject.toml:37`:
`git show origin/main:pyproject.toml | grep -nE 'data-files' -> 37:[tool.setuptools.data-files]`

**LD3 — The removal is proven where it matters: from an installed wheel, outside the checkout.** `cli-doctor.yml`'s `wheel-install` job gains one step after "Installed package resolves canonical schemas": from `/tmp`, the venv interpreter imports `agentmem_ref.runtime_config` and `agentmem_ref.discovery`, calls each module's schema loader (`runtime_config._configuration_schema()`, `discovery._probe_schema()` -- private names, because no public loader exists yet; #362 defines the public surface, and until then a rename that breaks this step is a rename that must update it), and exits 0 only if both return a dict whose `$id` ends with the expected file name; any exception exits 1 with the message printed. Without this, dropping `data-files` could break the installed package silently, since no test exercises the fallback today (brief section 1).
Grep-evidence for line 135 of `.github/workflows/cli-doctor.yml`:
`git show origin/main:.github/workflows/cli-doctor.yml | grep -nE 'Installed package resolves canonical schemas' -> 135:      - name: Installed package resolves canonical schemas`

**LD4 — In-process tests prove the three states each resolver can be in.** A new test module patches `receipts._SOURCE_SCHEMAS` and `receipts._packaged_schemas` (the two seams `schema_dir()` consults) rather than the filesystem: (a) source present -> both loaders return the canonical schema from `schemas/`; (b) source absent, packaged copy present (a temporary directory holding the two schema files) -> both loaders return that copy, which is the installed-wheel state in-process; (c) neither -> `RuntimeConfigurationError` and `DiscoveryInputError` respectively, each mentioning "install". Assertions are on the resolver's returned path, the loader's returned dict, and the raised type and message. **Observed on `origin/main` before locking**: (a) green; (b) red -- today's resolvers build the source path from `REPO_ROOT`, never from the `receipts` seams, so with the seams patched they still return the *source* path, and (b)'s path assertion fails; (c) red -- the loaders return dicts instead of raising. After Phase 2 all three are green.

## Phase 1: the tests

### Affected Files

- `reference/tests/test_packaged_schema_resolution.py` — new; one `TestCase`, three tests per LD4, a small context manager that patches the two `receipts` seams.

### Unit Tests

- `test_source_tree_resolves_both_schemas` — the resolved paths equal `schemas/<name>`, and each loader's `["$id"]` ends with its file name (both schemas carry `$id`: `schemas/runtime-configuration.schema.json:3`, `schemas/provider-probes.schema.json:3`).
- `test_packaged_copy_resolves_when_source_is_absent` — with `_SOURCE_SCHEMAS` pointed at a nonexistent directory and `_packaged_schemas` returning a temp dir holding copies of the two files, both resolvers return the path under that temp dir and both loaders return dicts equal to the canonical files. Red on `origin/main` on the path assertion (today's resolvers return the source path, since they read `REPO_ROOT`, not the seams).
- `test_neither_source_nor_package_raises_the_module_error` — with both seams pointed at nonexistent directories, `runtime_config._configuration_schema()` raises `RuntimeConfigurationError` and `discovery._probe_schema()` raises `DiscoveryInputError`, each message containing "install". Red on `origin/main`: the loaders return dicts.

## Phase 2: the resolvers and the packaging

### Affected Files

- `reference/agentmem_ref/runtime/runtime_config.py` — `_configuration_schema_path()` per LD1; removals per LD2.
- `reference/agentmem_ref/runtime/discovery.py` — `_probe_schema_path()` per LD1; removals per LD2.
- `pyproject.toml` — remove `[tool.setuptools.data-files]` (LD2).

### Unit Tests

- Phase 1's tests go green. The existing suite (which imports both modules widely: `test_cli_doctor.py`, `test_provider_discovery.py`, `test_configured_restart.py`, `test_domain_schema_discovery.py`) stays green.

## Phase 3: the wheel smoke

### Affected Files

- `.github/workflows/cli-doctor.yml` — one new step in `wheel-install` per LD3.

### Unit Tests

- The smoke is executed locally before the seal by the same recipe the job uses: `python -m build --outdir dist .`, install the wheel into a fresh venv, run the new step's script from a directory outside the checkout (on the Windows dev host the venv interpreter is `<scratch>/wheelvenv/Scripts/python.exe` and the outside directory is the scratchpad; CI uses `bin/python` and `/tmp`); exit 0 with both schema names printed. Also executed on the pre-fix tree with `data-files` removed but the resolvers unchanged, where it must exit 1 -- the negative that shows the smoke discriminates.

## Definition of Done

### Deliverable: one resolver

- **D1**: every schema the installed package reads comes from `_schemas/` through `receipts.schema_dir()`; `data-files` is gone.
- **D2**: `runtime_config.py` and `discovery.py` contain no `metadata` import, no `_DISTRIBUTION_NAME`, no `_..._DATA_SUFFIX`, no `_repo_root`; each `*_schema_path()` is under ten lines; `pyproject.toml` has no `data-files` table.
- **D3**: ledger SESSION SEAL (#41; audit VETO #38, VETO #39, PASS #40); `docs/GOVERNANCE_INDEX.md` plan row; `docs/FEATURE_INDEX.md` FX023; `docs/SYSTEM_STATE.md` counts; issue #365 updated after merge with what 3a closed and what this closes.
- **D4**: Phase 1's three tests pass after Phase 2; on `origin/main`, (b) and (c) are red and (a) is green, as observed; full suite 1121 + 3, 0 failures.

### Deliverable: the smoke discriminates

- **D1**: an installed wheel that cannot serve either schema fails `cli-doctor`'s `wheel-install` job.
- **D2**: the new step in `cli-doctor.yml`.
- **D3**: none beyond the seal.
- **D4**: local execution of the step's script from outside the checkout: exit 0 on the fixed wheel; exit 1 on a wheel built with `data-files` removed but the resolvers unchanged.

## Feature Inventory Touches

| entry_id | operation | test_path | test_descriptor |
|---|---|---|---|
| FX023 | NEW | `reference/tests/test_packaged_schema_resolution.py` | `runtime_config._configuration_schema()` and `discovery._probe_schema()` return the canonical schema from `schemas/` when present and from the packaged `_schemas/` copy when not, and raise their module errors naming "install" when neither exists |
| FX001 | MODIFIED | `.github/workflows/cli-doctor.yml` (`wheel-install`) | the installed wheel also serves `runtime-configuration` and `provider-probes` schemas from outside the checkout |

## CI Commands

- `python -m unittest reference.tests.test_packaged_schema_resolution` — LD4.
- `python -m unittest discover -s reference/tests -t reference` — full suite.
- `python -m build --outdir dist . && python -m venv <scratch>/wheelvenv && <scratch>/wheelvenv/bin/python -m pip install dist/*.whl` (Windows: `<scratch>/wheelvenv/Scripts/python.exe`) then the LD3 script from a directory outside the checkout — the smoke, locally.
- `python scripts/validate_schemas.py` and `python scripts/validate_fixtures.py fixtures` — unchanged surfaces stay clean.
- `python scripts/restructure_package.py --check` — layout unchanged.
- `python scripts/verify_seals.py` — anchors match.
