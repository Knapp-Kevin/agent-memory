# Research Brief: Sprint 3b — the visibility test under every CI discover style

**Date**: 2026-09-06
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 17.
**Implements**: a `main` defect surfaced by PR #386's CI, ruled into its own cycle by the operator on 2026-09-06 ("fix the visibility test in a follow up cycle")
**Risk**: L1 — one import line in one test file; no runtime module, schema, fixture or workflow changes

## 1. The defect, measured

`reference/tests/test_write_readable_visibility.py:20` reads:

```python
from .qualified_fixtures import corpus_for, registry_for, rule
```

It was written that way in #384 (`b6282dc`, ADR-037 step 4b-2), with a justification in the comment at lines 14-19: the module loads as `tests.X` under `discover -t reference` and as `reference.tests.X` under the targeted CI step, a relative import resolves under both, and "an absolute `from tests...` only works under the first."

That justification omits a third invocation style, and its last clause is false.

### 1a. Three invocation styles exist in CI

Every `python -m unittest` line under `.github/workflows/` was enumerated (73 lines, 47 workflows). They reduce to three ways a test module gets a name:

| Style | Invocation | Module name at import | Relative import | Workflows |
|---|---|---|---|---|
| A | `discover -s reference/tests -t reference` | `tests.test_write_readable_visibility` | resolves (`tests` is the package) | 20 workflows incl. `validate-doctrine-evidence.yml:38,153`, `write-readable-visibility.yml:29` |
| B | `python -m unittest reference.tests.test_write_readable_visibility` | `reference.tests.test_write_readable_visibility` | resolves (`reference.tests` is the package; `reference/` has no `__init__.py`, so it is a namespace package) | `write-readable-visibility.yml:26`, `p9-systems-characterization.yml:26`, `seal-anchors.yml:47` |
| C | `discover -s reference/tests -p 'test_*.py'` with `PYTHONPATH: reference` | `test_write_readable_visibility` (top-level; `-s` without `-t` makes `reference/tests` the top directory) | **fails**: `attempted relative import with no known parent package` | `evolveai-multicapability-qualification.yml:146-148`, `hermes-observe-govern-integration.yml:165-167` |

Style C is the "full Agent Memory reference regression" step of two integration workflows. Under C, unittest imports every test as a top-level module. Package-relative imports cannot resolve because there is no package.

### 1b. How every other consumer of `qualified_fixtures` imports it

Fifteen test files import the helper. All fifteen use the absolute form:

```
reference/tests/test_boundary_crossing.py:8            from tests.qualified_fixtures import corpus_for, registry_for, rule
reference/tests/test_canonical_and_derived_state.py:21 from tests.qualified_fixtures import corpus_for, registry_for, rule
reference/tests/test_deletion_completeness_evidence.py:10
reference/tests/test_epistemic_memory.py:6
reference/tests/test_fail_closed_review.py:32          from tests.qualified_fixtures import corpus_for, governed_adapter, rule
reference/tests/test_interchange.py:8
reference/tests/test_interchange_propagation.py:8
reference/tests/test_predictive_memory.py:6
reference/tests/test_procedural_memory.py:8
reference/tests/test_rejected_value_readmission.py:20
reference/tests/test_restart_safe_runtime.py:7
reference/tests/test_runtime_composition.py:7
reference/tests/test_semantic_readmission_adapter.py:7
reference/tests/test_semantic_readmission_fixture.py:8
reference/tests/test_structural_mutation_governance.py:9
```

The other test-local helpers follow the same convention: `from tests._maintenance_run_cases import` (2 files), `from tests import` (3 files). The visibility test is the only relative import under `reference/tests/` (`grep -lE '^from \.' reference/tests/test_*.py` returns one file).

### 1c. Why the absolute form also works under style B

Line 10 of the visibility test, unchanged since #310, inserts `reference/` at the front of `sys.path` before any project import:

```python
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
```

With `reference/` on `sys.path`, `tests` is importable as a top-level package under every style, including B. The #384 comment reasoned about `reference.tests.X` as the module name and did not account for the file's own path insert. Forty test files under `reference/tests/` carry the same insert.

### 1d. Verified empirically, both forms, all three styles

Run locally under the pinned validation venv (`cryptography==50.0.1`), from the repository root, on `origin/main` at `27f2de3`:

| Import form | A `discover -t reference` | B `reference.tests.X` | C `discover`, no `-t` |
|---|---|---|---|
| `from .qualified_fixtures import ...` (current) | OK | OK | **FAILED (errors=1)** |
| `from tests.qualified_fixtures import ...` (candidate) | OK | OK | OK |

The candidate was applied, all three styles run, and the file restored with `git checkout` before this brief was written; the working tree carries no change.

### 1e. Why it did not fail on `main`

Both style-C workflows are path-triggered. `evolveai-multicapability-qualification.yml` last ran on `main` at `03168da8` (2026-09-04), before #384 landed (`b6282dc`, 2026-09-05). `write-readable-visibility.yml`, which runs styles A and B only, has run green on `main` three times since (`9d97c97f`, `b6282dcf`, `27f2de39`). The defect was latent from the moment #384 merged and surfaced the first time a style-C workflow's paths were touched, which PR #386's package restructure did. CI job `101516308032` on that PR: `Ran 1111 tests`, `FAILED (errors=1, skipped=19)`, the one error being this import.

## 2. The minimal correction

Replace line 20 with the convention the other fifteen consumers use:

```python
from tests.qualified_fixtures import corpus_for, registry_for, rule
```

and rewrite the comment at lines 14-19 so it states what is actually true: the helper imports `agentmem_ref`, so it must load after the path insert; the absolute form resolves under all three CI invocation styles because of that insert; the relative form cannot resolve under `discover` without `-t`.

Nothing else moves. No workflow changes: adding `-t reference` to the two style-C steps would also work, but it would change two integration workflows to fix one test that is already out of convention, and it would leave the misleading comment in place. The one-line correction is the smaller change and the one that removes the cause.

## 3. What this cycle does not do

- It does not touch the Sprint 3a branch. PR #386 is held by the operator's ruling until this cycle and the DashClaw cycle land on `main`, after which #386 is rebased.
- It does not change the semantics of the visibility test, which asserts the ADR-037 4b-2 behaviour (a value correction commits only under an evaluator-held `TransitionRule`); only its import line and comment change.
- It runs on a branch from `origin/main`, whose ledger ends at Entry #25. The Sprint 3a branch numbers its own entries #26 and #27 and anchors `refs/seals/entry-26`. When #386 is rebased after this cycle lands, its entries renumber and its seal is re-made; that is the known cost of two cycles in flight, recorded here rather than discovered at rebase.
- The `refs/seals/entry-26` anchor already on `origin` belongs to the Sprint 3a branch's seal. `seal-anchors.yml:36,44` fetches `refs/seals/*` and runs `verify_seals.py`, which fails on an anchor with no matching ledger entry -- so on `main`, and on this branch, that workflow is red until the anchor is removed or #386 lands with a renumbered seal. Removing a remote ref is a remote mutation and is raised for the operator's decision, not performed in this cycle.
- It does not add a guard test for "no relative imports under `reference/tests/`". That would be a new invariant. It is recorded below as a candidate for the plan to accept or decline, not assumed.

## 4. Blueprint alignment

| Claim | Source | Actual finding | Status |
|---|---|---|---|
| "An absolute `from tests...` only works under the first [discover -t reference]" | `test_write_readable_visibility.py:18-19` (#384) | Works under A, B and C; `sys.path.insert` at line 10 makes `tests` importable everywhere | **DRIFT** — the comment is false and steered the file out of convention |
| "this module is loaded as `tests.X` under `discover -t reference` and as `reference.tests.X` by the targeted CI step" | same comment | True, but incomplete: two workflows load it as top-level `test_write_readable_visibility` | **DRIFT** — a third style was not considered |
| Tests under `reference/tests/` import helpers as `from tests.<helper> import` | 20 sites across 17 files | Holds for every file except this one | MATCH (convention), one outlier |
| `docs/ARCHITECTURE_PLAN.md` says nothing about test-module naming under discover | plan | Not a plan concern; no drift | MATCH |

## 5. Recommendations

1. **(this cycle, L1)** Change line 20 to the absolute form and correct the comment. Verify under all three styles and the full suite under style A (the 1117-test baseline, `+0`).
2. **(plan decision)** Whether to add a one-assertion guard to an existing layout-shaped test, "no `from .` imports under `reference/tests/`", so a future relative import fails in every style rather than only in the two style-C workflows. Cheap, but a new invariant; the Governor decides.
3. **(recorded, not this cycle)** The two style-C steps run a different module naming than the other 20 discover invocations. Unifying them on `-t reference` is a workflow-consistency item for a later cycle, not a defect.

## 6. Updated knowledge

Shadow Genome Failure #6 records the pattern: an import-constraint claim written in a comment, reasoned from module naming alone, never executed under the invocation it names, and omitting an invocation that exists in CI. The correct pattern is the one applied in section 1d: enumerate every invocation style CI uses and run the candidate under each before asserting which forms work.

---

_Research complete. Findings are advisory — implementation decisions remain with the Governor._
