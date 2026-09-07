# Plan: Sprint 3b — the visibility test loads under every CI discover style

**change_class**: hotfix
**doc_tier**: standard
**risk_grade**: L1
**research_artifact**: docs/research-brief-sprint3b-visibility-test-discover-2026-09-06.md (ledger Entry #26 on this branch)
**iteration**: 3, with the audit C1 addendum applied at implementation (iteration 1 numbered the feature-index row FX021; `main` ends at FX019, so the row is FX020 here and the Sprint 3a branch renumbers its FX020 at rebase. Iteration 3: grep-evidence restated one line per citation in the lint's canonical form; the 3a-branch layout-test citation removed because that file is not on `main`)

**boundaries**:
- limitations: the guard in Phase 2 checks import *form* under `reference/tests/`, not whether a module loads under each discover style; the three-style run in the brief's section 1d is the behavioural proof and is repeated in CI Commands, not encoded as a test.
- non_goals: unifying the two `discover` steps that run without `-t reference` (`evolveai-multicapability-qualification.yml:148`, `hermes-observe-govern-integration.yml:167`) onto the `-t reference` form; the DashClaw runner (its own cycle); any change to PR #386.
- exclusions: every file under `reference/agentmem_ref/`; every workflow; every fixture and schema; the semantics of `test_write_readable_visibility.py` beyond its import line and the comment that justifies it.

## Open Questions

None. The brief's one plan decision (add a guard or not) is taken below as LD3, with the reasoning stated so the audit can reject it.

## Locked Decisions

**LD1 — the import becomes the sibling convention.** Line 20 changes from `from .qualified_fixtures import corpus_for, registry_for, rule` to `from tests.qualified_fixtures import corpus_for, registry_for, rule`.
Grep-evidence for `reference/tests/test_write_readable_visibility.py:10`:
`git show origin/main:reference/tests/test_write_readable_visibility.py | grep -nE '^sys\.path' -> 10:sys.path.insert(0, str(Path(__file__).resolve().parents[1]))`
Grep-evidence for `reference/tests/test_write_readable_visibility.py:20`:
`git show origin/main:reference/tests/test_write_readable_visibility.py | grep -nE '^from \.' -> 20:from .qualified_fixtures import corpus_for, registry_for, rule`
Sibling form: `grep -lE '^from tests\.qualified_fixtures import' reference/tests/*.py -> 15 files` (listed in brief §1b).

**LD2 — the comment states what is true, nothing more.** Lines 14-19 are replaced by a comment saying: the helper imports `agentmem_ref`, so it must be imported after the path insert at line 10; that insert puts `reference/` on `sys.path`, which makes `tests` importable under all three CI invocation styles (`discover -t reference`, `python -m unittest reference.tests.X`, and `discover` without `-t`); a relative import cannot resolve under the third because the module is loaded top-level. The false clause ("only works under the first") is removed rather than reworded.
Grep-evidence for line 148 of `.github/workflows/evolveai-multicapability-qualification.yml` (under `env: PYTHONPATH: reference` at lines 146-147):
`git show origin/main:.github/workflows/evolveai-multicapability-qualification.yml | grep -nE "discover -s reference/tests -p" -> 148:run: python -m unittest discover -s reference/tests -p 'test_*.py'`
Grep-evidence for line 167 of `.github/workflows/hermes-observe-govern-integration.yml` (under `env: PYTHONPATH: reference` at lines 165-166):
`git show origin/main:.github/workflows/hermes-observe-govern-integration.yml | grep -nE "discover -s reference/tests -p" -> 167:run: python -m unittest discover -s reference/tests -p 'test_*.py'`

**LD3 — one guard test, because the defect was invisible to 45 of 47 workflows.** A new test file asserts that no test module under `reference/tests/` uses a package-relative import. The reason it earns its place: the failure mode surfaces only in two path-triggered integration workflows, which is why this defect sat on `main` for a day; the guard makes the same mistake fail under the 20 `discover -t reference` workflows and under the local suite. Per `doctrine-test-functionality.md`, the test does not assert on text alone: a helper `relative_imports(path) -> list[str]` parses the file with `ast` and returns the offending import statements; the test first proves the helper on a synthetic module written to a temporary directory (one relative import in, one statement out; a file with only absolute imports, empty list out), then applies it to every `reference/tests/test_*.py` and asserts the union is empty. (Audit C1: `test_*.py` only -- those are the modules unittest imports top-level; helpers are always imported as `tests.<helper>`, where a relative import resolves under every style.)

**LD4 — no workflow changes.** Adding `-t reference` to the two style-C steps would also fix the symptom, but it would change two integration workflows to accommodate one out-of-convention file, and it would leave the false comment in place. It is listed as a non-goal, not deferred work.

**LD5 — the guard uses `ast`, not a regex.** `ast.ImportFrom.level > 0` is the definition of a relative import; a regex on `^from \.` would miss `from . import x` written with leading whitespace inside a function and would match a docstring line. The Sprint 3a branch's layout test answers the same question over `agentmem_ref` with `ast`; that file is not on `main`, so on `main` the guard stands alone.

## Phase 1: the correction

### Affected Files

- `reference/tests/test_write_readable_visibility.py` — line 20 import form (LD1); lines 14-19 comment (LD2). No other line.

### Changes

Line 20: `from tests.qualified_fixtures import corpus_for, registry_for, rule`.
Lines 14-19: the comment per LD2, five lines or fewer.

### Unit Tests

- The existing `test_write_readable_visibility.py` suite is the behavioural check: it must produce the same result under all three invocation styles (CI Commands below). No new test in this phase.

## Phase 2: the guard

### Affected Files

- `reference/tests/test_test_import_convention.py` — new. `relative_imports(path: Path) -> list[str]` (module-level helper; `ast.walk`, collects `ast.unparse(node)` for every `ImportFrom` with `level > 0`) and one `unittest.TestCase`.

### Unit Tests

- `reference/tests/test_test_import_convention.py::test_helper_reports_a_relative_import` — writes a module with `from .helper import x` to a `tempfile.TemporaryDirectory`, asserts `relative_imports(path) == ["from .helper import x"]`; writes a module with `from tests.helper import x` and `import os`, asserts `[]`. Confirms the helper's output, not its presence.
- `reference/tests/test_test_import_convention.py::test_no_test_module_uses_a_relative_import` — applies the helper to every `reference/tests/test_*.py` (C1) and asserts the collected offenders (as `path:statement`) equal `[]`. On `origin/main` today this assertion fails with exactly one offender; after Phase 1 it passes.

## Definition of Done

### Deliverable: the visibility test loads under every CI discover style

- **D1**: `test_write_readable_visibility.py` imports its helper the way its fifteen siblings do, with a comment that is true.
- **D2**: line 20 reads `from tests.qualified_fixtures import corpus_for, registry_for, rule`; lines 14-19 carry no claim that the absolute form fails anywhere; `git diff --stat origin/main -- reference/tests/test_write_readable_visibility.py` shows one file, and the diff touches only lines 14-20.
- **D3**: ledger SESSION SEAL entry for this plan on this branch (#27, following the research brief at #26); `docs/GOVERNANCE_INDEX.md` row for the plan; Shadow Genome Failure #6 resolution row moves from OPEN to FIXED naming the seal entry; `docs/SYSTEM_STATE.md` test-file and test counts.
- **D4**: the three CI invocation styles below each exit 0 on `test_write_readable_visibility`; the full suite under `discover -t reference` runs 1109 + N tests with 0 failures where N is the guard's test count (2), 7 skipped under the pinned venv.

### Deliverable: the guard

- **D1**: a relative import in any test module under `reference/tests/` fails the suite everywhere, not only in two path-triggered workflows.
- **D2**: `reference/tests/test_test_import_convention.py` with `relative_imports(path: Path) -> list[str]` and the two tests named above.
- **D3**: `docs/FEATURE_INDEX.md` row (test-infrastructure guard, `verified`); counted in `docs/SYSTEM_STATE.md`.
- **D4**: `test_helper_reports_a_relative_import` passes (synthetic in, exact statement out); `test_no_test_module_uses_a_relative_import` passes after Phase 1 and is shown to fail when Phase 1's line 20 is reverted to the relative form (adversarial negative, recorded in the seal).

## Feature Inventory Touches

| entry_id | operation | test_path | test_descriptor |
|---|---|---|---|
| FX020 | NEW | `reference/tests/test_test_import_convention.py` | `relative_imports(path)` returns the relative `ImportFrom` statements of a module; every `reference/tests/*.py` yields none |

## CI Commands

- `python -m unittest discover -s reference/tests -t reference` — full suite, style A (the 20 `-t reference` workflows).
- `python -m unittest reference.tests.test_write_readable_visibility` — style B (`write-readable-visibility.yml:26`).
- `PYTHONPATH=reference python -m unittest discover -s reference/tests -p 'test_write_readable_visibility.py'` — style C (`evolveai-multicapability-qualification.yml:148`, `hermes-observe-govern-integration.yml:167`), the invocation that failed.
- `python -m unittest reference.tests.test_test_import_convention` — the guard.
- `python scripts/validate_schemas.py` and `python scripts/validate_fixtures.py fixtures` — unchanged surfaces stay clean.
- `python scripts/verify_seals.py` — expected to report the stray `refs/seals/entry-26` anchor until the operator's decision on it (brief §3); recorded, not masked.
