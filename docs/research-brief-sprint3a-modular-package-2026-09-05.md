# Research Brief: Sprint 3a — modular package structure for `agentmem_ref`

**Date**: 2026-09-05
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 16.
**Implements**: the operator's instruction of 2026-09-05 — "modular package structure makes sense, proceed" — and ADR-035/ADR-036's requirement that Agent Memory's Code Reality Graph be a named first-party module

## 1. What exists, measured

`reference/agentmem_ref/` is **126 flat modules and zero subpackages** (the one directory is `__pycache__`). The twelve largest run 558–805 lines. Prefix clustering is real but informal: `security_*`, `runtime_*`, `maintenance_*`, `derivation_*`, `dashclaw_*`, `codegenome_*`, `temporal_*`, `precedent_*` and so on — organisation the filenames imply and the package does not express.

The dependency graph (relative imports, including lazy ones) has a clear shape:

| In-degree | Module | Role |
|---|---|---|
| 47 | `receipts` | schema validation, decision receipts |
| 39 | `policy` | the PAMA evaluator |
| 23 | `adapter` | `GovernedMemoryAdapter` |
| 19 | `substrate` | `TemporalGraphPort`, `InMemoryTemporalGraph` |
| 12 | `capabilities` | capability contract |
| 9 | `evidence_qualification` | R3/R2 (Loop 9) |
| 8 | `qualification` | provider qualification |
| 7 | `projections` | derived-state declarations |

Fourteen modules import nothing internal; 59 are imported by nothing internal (leaf harnesses and comparators). **One import cycle**: `pending_verification ↔ resumption`, already broken by a lazy import inside `resume()` (Loop 10), so it is a design note rather than a blocker.

## 2. The external surface is large, and it decides the method

**119 distinct modules are referenced from outside the package, 427 times** — tests, every `run_*.py`, three examples, two docs, five workflows. A physical move without compatibility at the old paths would break essentially everything at once, and "fix 427 references" is not a refactor, it is a rewrite with a refactor's name.

So old paths must keep working. But **the obvious shim is wrong.** A shim of the form

```python
from .core.policy import *
```

creates a *second* module object. `policy._HIGH_RISK` is monkeypatched by tests (Loops 11–12) and read by `strength_ladder_for` at call time; a `*`-import shim would let the test patch the shim's copy while the real module reads its own — a silent divergence, and underscore names are not re-exported at all.

The correct technique makes the old path **the same module object**:

```python
# agentmem_ref/policy.py  (compatibility alias)
import sys
from .core import policy as _real
sys.modules[__name__] = _real
```

`agentmem_ref.policy is agentmem_ref.core.policy` — identity, attributes, monkeypatches, all preserved. That identity is the property to test, per shim.

## 3. Two hazards that a naive move breaks silently

**Path resolution keyed to `__file__` depth.** Twenty-two sites compute repository or package roots as `Path(__file__).resolve().parents[2]` (or `[1]`). Moving a module one directory deeper shifts every one by one — and `receipts.schema_dir()` is among them, so every schema validation would fail to find the source tree and fall through to the packaged copy or a `FileNotFoundError`. `receipts._packaged_schemas` also uses `resources.files(__package__)`, which would resolve to the *subpackage* and miss `_schemas/`.

This is the single largest hazard and it has a clean fix that is an improvement on its own: one `_paths.py` at the package top level exposing `PACKAGE_ROOT` and `REPO_ROOT`, computed once, with every site importing them. Depth-coupling is removed rather than re-tuned.

**Documentation file paths.** 69 distinct `reference/agentmem_ref/<name>.py` paths appear in `docs/`, the wiki source and READMEs, most in `FEATURE_INDEX.md`. After the move they point at three-line aliases. Every one is updated in this cycle, and the alias files carry a one-line pointer to the real location so a stale reference elsewhere still lands somewhere useful.

No module-path strings are baked into evidence: no `__module__`, `__qualname__` or pickle use anywhere in the package, so emitted artefacts do not change.

## 4. Packaging is already compatible

`pyproject.toml` uses `[tool.setuptools.packages.find]` with `include = ["agentmem_ref*"]`, so subpackages are discovered automatically. `package-data` covers `agentmem_ref/_schemas/*.json` at the top level, which stays where it is. The console entry point is `agentmem_ref.cli:main`; the `cli` alias keeps it valid without touching `pyproject.toml`. The wheel-install job exercises `agent-memory --help`, `config validate` and `doctor`, which is the packaged surface to re-verify.

## 5. The layering the graph supports

Derived from the dependency direction, not from filenames:

| Subpackage | Contents | Depends on |
|---|---|---|
| `core/` | `policy`, `receipts`, `evidence_qualification`, `verification`, `pending_verification`, `resumption`, `readmission`, `contextual_recall`, `governance_projection`, `portable_evidence` | nothing outside `core` |
| `substrate/` | `substrate`, `graphiti_driver`, `projections`, `residue`, `visibility` | `core` |
| `capabilities/` | `capabilities`, `qualification`, `component_fallback`, `component_failure_probe`, `hindsight_qualification`, `memos_qualification`, `resource_provider_substitution`, `resource_exchange`, `evolveai_profile` | `core` |
| `crg/` | `code_graph_qualification`, `codegenome_profile`, `codegenome_cognitive_mesh`, `codegenome_scope_residue` | `core`, `capabilities`, `memory` |
| `runtime/` | `adapter`, `restart_runtime`, `configured_restart`, `runtime_composition`, `runtime_config`, `runtime_behavior`, `doctor`, `cli`, `discovery`, `composition`, `contextual_recall_adapter`, `projection_governance`, `semantic_readmission_adapter`, `write_claims`, `scope_governance`, `shared_revocation` | `core`, `substrate`, `capabilities` |
| `memory/` | the governed memory kinds and their evidence: `cognitive_mesh`, `epistemic_memory`, `predictive_memory`, `procedural_memory`, `decision_overwrite`, `reusable_grants`, `structural_*`, `domain_schema_mutation`, `crossing`, `interchange*`, `deletion_completeness`, `derivation_*`, `temporal_*`, `precedent_*`, `maintenance_run*`, `dashclaw_*`, `evolveai_cognitive_mesh`, and the evidence modules | `core`, `substrate`, `runtime` |
| `harness/` | every `*_harness`, `*_depth`, `*_comparator`, `*_characterization`, `benchmark_*`, `forbidden_hits`, `concurrency_evidence`, `long_horizon_*`, `operational_memory_benchmark`, `security_evidence_depth`, `fixture_conformance`, `logical_state_algebra_pressure`, `architecture_family_*` | anything — leaves |

**`crg/` is the module ADR-035 and ADR-036 asked for.** ADR-035: "CodeGenome is the initial first-party implementation of the Code Reality Graph." ADR-036 and the operator's ruling: same-owner components are first-party and are named as Agent Memory's own. So the Code Reality Graph is `agentmem_ref.crg`, and the CodeGenome modules are its implementation profile inside it — not an attributed provider bolted on beside it.

## 6. What this is not

It is **not** #362. #362 is the public consumer API — versioned input types, an approval stage, a JS-runtime reconciliation. That is Sprint 4's boundary freeze and its blast radius is deliberate. This cycle changes where modules live and nothing about what they expose; `agentmem_ref.__init__` keeps exactly its five exports. A layout that makes the boundary *visible* is a precondition for freezing it well, and that is all this claims.

## 7. Blast radius and the invariant

Every file in the package moves. The invariant is therefore behavioural, not textual: **1109 tests unchanged and green, every `run_*.py` green, the wheel smoke green, `verify_seals` green, and every old import path the identical object to its new one.** Unlike Loop 14, no outcome is meant to change; a changed test here is a regression by definition.

## 8. Risk grade

**L3.** Nothing about governance semantics moves, but everything about where it lives does, and the two silent hazards in §3 are the kind that pass a green suite until the wheel is installed somewhere else.

## 9. Next

`/qor-plan`.
