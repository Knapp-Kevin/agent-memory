# Research Brief: Sprint 3d — what remains of #365 after the layered package, and what comes after

**Date**: 2026-09-06
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 19.
**Target**: the open issue set after Sprints 3a-3c merged (`main` at `7caaa52`): #365 (wheel-safe packaging remainder), #362 (public consumer API), #364 (recall authority legs), #363 (production state profile), #392 (DashClaw transition rules)
**Scope**: size each, verify what Sprint 3a already closed, and recommend the next loop

## Executive summary

Sprint 3a closed most of #365 without being asked to: the "14 emitter loaders" that resolved by `Path(__file__)` walking are gone (zero such sites remain in the package outside `_paths.py`). What remains of #365 is two `importlib.metadata` fallbacks that look for `data-files` entries the wheel no longer needs, and the `[tool.setuptools.data-files]` section itself. That is a one-loop, L2 change with an existing wheel-install smoke to extend. #362 is a boundary freeze by design (large blast radius, an approval stage that does not exist, a diverging JS surface) and is a `/qor-ideate` candidate, not a plan. Recommendation: Loop 19 closes #365; Loop 20 opens Sprint 4 through ideation.

## Findings

### 1. #365 — the remainder, measured on `main` after 3a

| Claim in #365 ("still open") | On `main` `7caaa52` | Status |
|---|---|---|
| "14 emitter loaders still resolve by `Path(__file__)` walking" | `grep -rnE 'Path\(__file__\)' reference/agentmem_ref --include=*.py` minus `_paths.py`: **0 hits**. Sprint 3a replaced 22 `parents[N]` sites with `REPO_ROOT` / `REFERENCE_ROOT` / `PACKAGE_ROOT` from `reference/agentmem_ref/_paths.py` (Entry #36). | **closed by 3a**, not yet recorded on the issue |
| "the two `data-files` fallbacks in `runtime_config` and `discovery`" | Present. `reference/agentmem_ref/runtime/runtime_config.py:226-247` `_configuration_schema_path()`: source tree first, then `metadata.files("agent-memory-reference")` scanning for the suffix `agent_memory_reference/schemas/runtime-configuration.schema.json` (`:40`), else `RuntimeConfigurationError`. `reference/agentmem_ref/runtime/discovery.py:23,81-93`: the same shape for `provider-probes.schema.json`. | open |
| "`data-files` itself should go" | `pyproject.toml:37-41` still declares `[tool.setuptools.data-files]` with exactly those two schemas under `agent_memory_reference/schemas`. | open |
| "`schemas/` must not be physically moved" | Unchanged; `setup.py:13-27` copies `schemas/` into `agentmem_ref/_schemas/` at build time and refuses an empty copy; `pyproject.toml:34-35` ships `_schemas/*.json`; all 58 schemas, including `runtime-configuration.schema.json` and `provider-probes.schema.json`, are in the packaged copy. | holds |

The resolver the two fallbacks should use already exists: `reference/agentmem_ref/core/receipts.py:37-44` `schema_dir()` returns the source tree when present and the packaged `_schemas/` otherwise, raising `FileNotFoundError` with an install hint when neither exists. Sprint 3a's audit C1 proved it from an installed wheel run outside the checkout. Neither `runtime_config` nor `discovery` imports `receipts`; both carry their own two-path lookup keyed to `data-files` entries that duplicate what `_schemas/` already carries.

**Coverage gap**: no test under `reference/tests/` references `_configuration_schema_path`, the probe-schema lookup, `metadata.files`, or the `data-files` suffixes (`grep` returns nothing). The wheel-install smoke in `cli-doctor.yml` (`wheel-install` job) proves `receipts` resolution and `agent-memory --help` from outside the checkout; it does not touch `runtime_config` or `discovery`. So the two fallbacks are exercised only by CI jobs that happen to install the wheel and run those modules, if any do.

**Minimal correction (for the plan)**: both modules resolve their schema through `receipts.schema_dir()`; the `metadata` import, the two `_..._DATA_SUFFIX` constants and the `[tool.setuptools.data-files]` section are removed; the wheel smoke gains two assertions from outside the checkout -- `runtime_config` loads its schema and `discovery` loads the probe schema from the installed package -- so the removal is proven where it matters. `runtime` may import `core` (layer order `core < ... < runtime`), so the dependency direction is already permitted. Risk L2: packaging and two runtime modules' schema lookup; behaviour of the resolved schema unchanged.

### 2. #362 — public consumer API

Verified on `main`: `reference/agentmem_ref/__init__.py:9-13` exports `adapter, governance_projection, policy, receipts, substrate`; `Proposal` (`core/policy.py:121`), `CommitResult` (`runtime/adapter.py:77`), `AdmissionResult` (`:88`), `RecallContext` (`:102`), `Episode` / `Fact` (`state/substrate.py:43,54`) are dataclasses with no schema; 58 schemas cover the outputs; the JS runtime at `integrations/agent-memory-runtime/src/index.mjs` still exists as a second surface. The issue's own framing -- "blast radius is large by construction; that is the point of freezing it deliberately" -- and the missing approval stage (PRD-001 propose / decide / approve / commit) make this a concept decision before it is a plan: which types become the versioned contract, whether the approval stage is a new governed seam or the existing qualified-evidence discharge under a name, and what happens to the JS surface. Per the standing cycle, new concepts go through `/qor-ideate` before `/qor-plan`. Not sized here beyond: 55 importers of `GovernedMemoryAdapter`; 50 `RecallContext(` sites in 27 files and 70 `governed_recall(` sites in 25 files (from #364).

### 3. #364, #363, #392

- **#364** three legs remain (caller-asserted `principal_ref`, shared-domain membership, write-side crossing never mutating `_fact_scope`). The first is a recorded trust-boundary decision (host authenticates); the other two touch the same `RecallContext` / adapter surface #362 will freeze. Sequencing them after #362 avoids changing that surface twice.
- **#363** is Sprint 6 in the remediation plan and depends on the port boundary #362 defines.
- **#392** is blocked on a DashClaw-side decision about rule authorship.

## Blueprint alignment

| Claim | Source | Finding | Status |
|---|---|---|---|
| 14 emitter loaders still walk `Path(__file__)` | issue #365 | 0 remain after Entry #36 | **DRIFT** -- the issue is stale; to be updated when Loop 19 closes it |
| `data-files` is still needed for `runtime_config` / `discovery` | `pyproject.toml:37-41` | `_schemas/` already carries both schemas; `receipts.schema_dir()` resolves them | **DRIFT** -- redundant packaging path |
| The wheel smoke proves packaged-schema resolution | `cli-doctor.yml` wheel-install | for `receipts` only | MATCH with a gap |
| #362 is plan-ready | -- | it is a boundary freeze with an undesigned approval stage | needs `/qor-ideate` |

## Recommendations

1. **Loop 19 (this cycle), L2**: close #365 -- route both modules through `receipts.schema_dir()`, drop `data-files`, extend the wheel smoke to both modules, update the issue with what 3a already closed. `/qor-plan` next.
2. **Loop 20**: open Sprint 4 (#362) with `/qor-ideate`: the versioned input contract, the approval stage, the JS surface.
3. **After Sprint 4**: #364 legs 2-3 and #363 against the frozen boundary.

## Updated knowledge

Sprint 3a's `_paths.py` retired the emitter-loader half of #365 as a side effect of removing depth-coupled path resolution; issues closed by side effect must be re-measured, not carried forward from their last text.

---

_Research complete. Findings are advisory — implementation decisions remain with the Governor._
