# Plan: Sprint 3a — modular package structure for `agentmem_ref`

**change_class**: feature (gate-schema class; the change is a non-breaking layout refactor)
**Risk Grade**: L3
**Session**: 2026-09-05T1400-b7a3e1
**Research**: `docs/research-brief-sprint3a-modular-package-2026-09-05.md`
**Iteration**: 3 (amended for audit V1-V3; layer names for package shadowing, found at implementation)
**Implements**: operator instruction 2026-09-05; ADR-035/036's named first-party Code Reality Graph module

## Objective

Turn 126 flat modules into seven subpackages that express the dependency layering the graph already has, name Agent Memory's Code Reality Graph as `agentmem_ref.crg`, and change **no behaviour**: every old import path stays valid and is the identical module object.

## The invariant, stated first

This is the opposite of Loop 14. There, outcomes were meant to change and the baseline was not a target. Here **the baseline is the deliverable**: 1109 tests unchanged and green, every `run_*.py` green, the wheel smoke green, `verify_seals` green. A changed test is a regression by definition, and the only new tests are the ones that prove the aliases are identity-preserving.

## Boundaries

**In scope**: the seven subpackages in the research brief's §5; a `sys.modules` alias at every old path; `_paths.py`; the 22 `__file__`-depth sites; the 69 documentation paths; a generator script so the move is reproducible; an identity test.

**Out of scope**: #362 (public API, versioned input types, approval stage — Sprint 4). `agentmem_ref.__init__` keeps exactly its five exports. No function, class, signature, schema, fixture, or policy changes. No alias is removed — that is a later cycle, once importers are migrated.

## Design decisions

**LD1 — Layering follows the dependency graph, not the filenames, and the order is stated once (audit V1).**

```
core < state < contracts < runtime < memory < crg < harness
```

**Layer names must not collide with module names.** A subpackage directory shadows a same-named module file on the import path, so `substrate.py` cannot keep its alias beside a `substrate/` package — `agentmem_ref.substrate` would resolve to the package, and every `from agentmem_ref.substrate import InMemoryTemporalGraph` would break. The state layer (substrate, drivers, projections, residue, visibility) is therefore `state`, and the capability-contract layer is `contracts`. The mover asserts that no layer name is also a module name.

`core` imports nothing outside itself; `state` and `contracts` import `core`; `runtime` imports those; `memory` imports `runtime` and below; `crg` sits **above** `memory` because `codegenome_cognitive_mesh` imports `cognitive_mesh` and nothing in `memory` imports `crg`; `harness` is leaves and may import anything. The assignment table and this order live in one place — `scripts/restructure_package.py` — and the layout test **reads them from there**, so the test cannot be written to a different order than the mover. Rule: **no subpackage may import from a subpackage later in the order.** That is what makes the layering true rather than decorative.

**LD2 — Old paths are the same object, not a copy.**
Each old module path becomes a three-line alias that assigns `sys.modules[__name__]` to the real module. `agentmem_ref.policy is agentmem_ref.core.policy`. A `from X import *` shim would create a second object, drop underscore names, and let a test monkeypatch a copy while the evaluator reads the original — exactly the silent divergence Loops 11–12's `_HIGH_RISK` tests exist to catch. Identity is asserted for every alias.

**LD3 — Path resolution is decoupled from depth, once.**
`agentmem_ref/_paths.py` exposes `PACKAGE_ROOT` and `REPO_ROOT`, computed at the top level. All 22 `Path(__file__).resolve().parents[N]` sites import them. `receipts._packaged_schemas` uses the top-level package name explicitly rather than `__package__`, so `_schemas/` resolves from a subpackage. This removes the hazard rather than re-tuning `N`, and it is an improvement independent of the move.

**LD4 — `crg` is Agent Memory's Code Reality Graph, and CodeGenome is its profile.**
ADR-035: "CodeGenome is the initial first-party implementation of the Code Reality Graph." ADR-036 and the operator's ruling: same-owner components are first-party and named as Agent Memory's own. So the subpackage is `crg`, its docstring says what a Code Reality Graph is, and `codegenome_*` live inside it as the implementation profile — not as an attributed provider beside it.

**LD5 — The move is a script, not a session.**
`scripts/restructure_package.py` holds the assignment table, moves files with `git mv` (history preserved), rewrites each module's relative imports to the new layout, and writes the aliases. It is idempotent and refuses to run on a dirty tree. A move of 126 files done by hand is a move nobody can review; a move done by a script is one diff plus one table.

**LD6 — Relative imports are rewritten to the new layout; aliases are for outsiders — including `__init__` (audit V2).**
Inside the package, `from . import policy` becomes `from ..core import policy` (or the package-relative form the layer needs). Internal code does not route through aliases, so the aliases carry only external compatibility and can be removed later without touching the package. `agentmem_ref/__init__.py` is internal code: it imports the five exports from their new locations and re-binds the same five names, so the exported surface is byte-identical without an alias in the path.

**LD9 — Three residents stay at the top level (audit V3).**
`__main__.py` (`python -m agentmem_ref`), `_schemas/` (package-data, resolved by `_paths`), and `_paths.py` itself are neither moved nor aliased. The mover's table carries an explicit `STAYS` set so a rerun never treats them as unassigned.

**LD7 — Every documentation path is updated, and aliases point home.**
The 69 `reference/agentmem_ref/<x>.py` references are rewritten to the new locations. Each alias file's one docstring line names the real location, so a reference missed anywhere else still lands on a signpost.

**LD8 — Lazy-import cycle stays lazy.**
`pending_verification ↔ resumption` is broken by a lazy import inside `resume()` (Loop 10). Both land in `core`, the lazy import is rewritten to the new relative path, and the cycle test from Loop 10 keeps guarding it.

## Affected files

| Change | Count |
|---|---|
| Modules moved into `core/ state/ contracts/ runtime/ memory/ crg/ harness/` | 124 (plus `__init__`, `__main__` staying) |
| Alias files written at the old paths | 124 |
| New: `_paths.py`, seven `__init__.py`, `scripts/restructure_package.py`, `reference/tests/test_package_layout.py` | 10 |
| `__file__`-depth sites rewritten | 22 |
| Documentation paths rewritten | 69 |

`pyproject.toml` unchanged (`packages.find` includes `agentmem_ref*`; entry point resolves via the `cli` alias).

## Definition of Done

1. **Every old import path resolves to the identical object as its new path** — `agentmem_ref.X is agentmem_ref.<layer>.X` for all 124 moved modules, asserted by enumeration.
2. **Monkeypatching through an alias reaches the real module**: `agentmem_ref.policy._HIGH_RISK = (...)` is observed by `agentmem_ref.core.policy.strength_ladder_for` (LD2).
3. **No subpackage imports from a layer later in the stated order** (LD1), asserted by parsing every module's imports against the order **read from `restructure_package.py`**, not a copy in the test.
3b. `__init__.py` contains no import that resolves through an alias (LD6, audit V2).
3c. `__main__.py`, `_schemas/` and `_paths.py` are present at the top level and absent from the alias set (LD9, audit V3).
4. **No `Path(__file__).resolve().parents[N]` remains** in the package (LD3); `receipts.schema_dir()` resolves the source tree, and — in a scratch venv with the wheel installed and the source tree absent — resolves the packaged `_schemas/`.
5. **1109 tests pass, unchanged**: `git diff --stat reference/tests` touches only the new layout test. Any other test change fails DoD.
6. Every `run_*.py` CI invokes exits 0; `verify_seals.py` green; validators clean; wheel smoke (`agent-memory --help`, `config validate`, `doctor`) green in a fresh venv.
7. `agentmem_ref.__init__` exports exactly `adapter, governance_projection, policy, receipts, substrate`, unchanged.
8. **Zero `reference/agentmem_ref/<name>.py` references remain that point at an alias** in `docs/`, `wiki-src/`, READMEs and workflows (LD7) — excluding sealed historical records (`META_LEDGER.md`, earlier sprint plans and research briefs, JSON evidence records), whose content hashes are ledger-bound and which describe the layout as it was when they were sealed.
9. `restructure_package.py --check` reports the tree already matches its table (idempotence), and refuses on a dirty tree.
10. `git log --follow` on a moved module shows its pre-move history (LD5).
11. `agentmem_ref/crg/__init__.py` states that it is Agent Memory's Code Reality Graph and that CodeGenome is its first-party implementation profile (LD4).

## CI Commands

```
python -m unittest discover -s reference/tests -t reference
python scripts/verify_seals.py
python scripts/validate_schemas.py
python scripts/validate_fixtures.py fixtures
```

## Rollback

`git revert` of the single squash commit restores the flat layout; the aliases were only ever additive.

## Next

`/qor-audit`. L3, adversarial: whether any alias is a copy rather than the object; whether any path-resolution site survives the sweep; whether the layering claim is checked or merely asserted; whether anything about the public surface moved under the name of a refactor.
