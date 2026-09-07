# Research Brief

**Date**: 2026-09-01T22:00:00-04:00
**Analyst**: The Qor-logic Analyst
**Target**: Sprint 1 "install correctness" of `docs/RESEARCH_BRIEF.md` (Loop 1 of the ADR-035 build-toward program)
**Scope**: GAP-ARCH-03, GAP-RT-01 (hot slice), GAP-RT-02, GAP-RT-03, GAP-DOC-09, GAP-DOC-13, GAP-CI-05, GAP-DOC-01 (badge only), wheel-install CI check. Exclusions: `schemas/` is not moved; no authority-path changes; no issue creation; no commits.
**Session**: 2026-09-02T0158-2a109f
**Input**: `docs/RESEARCH_BRIEF.md` Rounds 1-3 evidence (not re-run)

---

## Executive Summary

Every interface Sprint 1 touches was verified against source. The packaging mechanism the plan depends on (build-time copy of root `schemas/` into the package plus an `importlib.resources` fallback) was prototyped end to end and works with the repo's setuptools 79 and `python -m build`. Two drifts from the deep-audit brief: GAP-DOC-13 is overstated because `docs/CONFIGURATION.md:326` already disclaims the listed commands as unimplemented, and the `.gitignore` working copy has mixed line endings, which `.gitattributes` will normalize. No target file has changed since 2026-08-15, so the brief's citations are current.

## Findings

### 1. Dependencies (GAP-ARCH-03)

- **Location**: `pyproject.toml:12-14` declares `jsonschema>=4.20,<5` only. `reference/requirements.txt:3-7` pins `jsonschema==4.26.0`, `cryptography==50.0.0`, `agent-manifest==0.11.0`, `agentrust-trace==0.8.0`, `rfc8785==0.1.4`.
- **Consumers**: 49 of 58 workflows install `reference/requirements.txt`; two workflows run `pip install .` from the repository root (`cli-doctor.yml:26`, `provider-discovery.yml:26`; corrected after audit V2, the original grep pattern could not match a trailing ` .`); `CONTRIBUTING.md:205-226` documents the requirements-file install and scopes "stdlib-only" to validators with `jsonschema` as the exception.
- **Implication**: 17 modules import `cryptography`/`rfc8785` unguarded (brief, verified in venv). Two options preserve the 49 workflows unchanged: (a) hard deps `cryptography>=50,<51` and `rfc8785>=0.1,<0.2` in `[project.dependencies]`; (b) an extra such as `[project.optional-dependencies] evidence = [...]`. `agent-manifest` and `agentrust-trace` are comparator-only (`requirements.txt:2` comment) and belong in a `comparators` extra, not hard deps.
- **Verified Against Blueprint**: DRIFT. `ARCHITECTURE_PLAN.md` Dependencies table lists jsonschema as "the single runtime dependency"; reality requires cryptography and rfc8785 for 17 of 120 modules.

### 2. Wheel-safe schema loading, hot slice (GAP-RT-01)

- **Location**: `reference/agentmem_ref/receipts.py:28` `SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"`; `:42-45` `_validator` reads `SCHEMA_DIR / schema_name`. Installed, `SCHEMA_DIR` resolves to `<venv>/Lib/schemas` (does not exist; reproduced in `scratchpad/venv-verify`).
- **Existing fallback pattern**: `runtime_config.py:221-247` and `discovery.py:70-96` try the source path, then walk `importlib.metadata.files(_DISTRIBUTION_NAME)` for a suffix match on the `data-files` entries declared at `pyproject.toml:26-30`. Those entries install to `<prefix>/agent_memory_reference/schemas/` (verified: `venv-verify/agent_memory_reference/schemas/*.json`), outside `site-packages`. `data-files` is deprecated in setuptools.
- **No package-local schema dir exists** (`reference/agentmem_ref/schemas` absent; no `MANIFEST.in`).
- **Mechanism verified (prototype `scratchpad/pkgproto`)**: `setup.py` subclassing `setuptools.command.build_py` copies `<root>/schemas/*.json` into `<pkg>/_schemas/` before the standard build; `[tool.setuptools.package-data] agentmem_ref = ["_schemas/*.json"]` includes them. `python -m build --wheel` produced `proto_pkg/_schemas/a.schema.json` inside the wheel; after `pip install` in a fresh venv, `resources.files(__package__) / "_schemas"` resolved and the file existed. Source checkouts keep using root `schemas/` (source path checked first). setuptools 79.0.0 and build 1.2.2 are present locally. The generated `_schemas/` directory must be gitignored.
- **Scope of the slice**: only `receipts.py:28` is on the commit/delete hot path (brief Round 2). The 14 emitter-only loaders and the two `data-files` fallbacks are Sprint 3.
- **Verified Against Blueprint**: MATCH for the CLI contract; DRIFT for the blueprint's implicit assumption that the installed package is usable (`ARCHITECTURE_PLAN.md` "Reference runtime CLI" contract).

### 3. Cedar digest and line endings (GAP-RT-02)

- **Location**: `cedar_policy_comparator.py:40` `CEDAR_POLICY_PATH` (`reference/policies/cedar_agent_memory_v01.cedar`), `:41` `CEDAR_POLICY_SHA256 = "sha256:a369c142..."`, `:138-141` `policy_sha256` hashes `read_bytes()` raw.
- **Index state**: `git ls-files --eol`: 843 `i/lf w/crlf`, 6 `-text`, 1 `none`, 1 `i/lf w/mixed` (`.gitignore`, from this session's appends). `core.autocrlf=true`. Zero `i/crlf`, so a `.gitattributes` with `* text=auto eol=lf` changes no committed blob; only Windows working trees renormalize.
- **Fix shape**: two independent parts. (a) `.gitattributes` so the working tree matches the index. (b) Normalize before hashing in `policy_sha256` (`data.replace(b"\r\n", b"\n")`) so the pin is byte-order-mark and EOL independent regardless of checkout. The LF-normalized digest equals the pin (brief Round 1).
- **Other digests**: only this pin covers a tracked file; qualification digests hash parsed JSON (EOL-safe). The atlas inventory lock (`validate_atlas_research_scaffold.py:44-49`) hashes a tracked file and currently mismatches on Windows; `.gitattributes` fixes it as a side effect.
- **Verified Against Blueprint**: MATCH (governance controls section anticipated `.gitattributes` is absent).

### 4. Version-asserting tests (GAP-RT-03)

- **Location**: `reference/tests/test_agent_manifest_correlation.py:56` class-level `@unittest.skipIf(MemoryCheckpoint is None, ...)` guards import absence only; `:150-153` asserts `importlib.metadata.version("agent-manifest") == "0.11.0"`. `reference/tests/test_trace_action_evidence.py:117-122` asserts `importlib.metadata.version("agentrust-trace") == "0.8.0"` with no guard; raises `PackageNotFoundError` when absent.
- **Repo idiom**: `unittest.skipIf` / `unittest.skipUnless` with a module-level availability probe (`test_graphiti_substrate.py:57` `graphiti_available()`). The suite runs under `unittest discover` in CI (`validate-doctrine-evidence.yml`), not pytest, so guards must be `unittest` decorators.
- **Fix shape**: a helper that returns the installed version or `None` via `importlib.metadata` catching `PackageNotFoundError`, and `skipUnless(installed == pinned, ...)` on the two pin-identity tests only. The rest of each class keeps its current guard so behavioural tests still run when the package is present at any version.
- **Verified Against Blueprint**: n/a (test hygiene).

### 5. Stale "Proposed" language (GAP-DOC-09) and phantom CLI commands (GAP-DOC-13)

- **DOC-09 sites verified** (7): `docs/future/multi-agent-shared-memory-protocol.md:5` (ADR-022); `docs/profiles/policy-projection-compatibility-profile.md:3` (ADR-030); `docs/profiles/temporal-commitment-evidence-profile.md:3` (ADR-031); `docs/programs/runtime-evidence/cognitive-mesh.md:3,190` (ADR-035); `wiki-src/Runtime-Evidence.md:73` (ADR-020), `:75` (ADR-022). ADR headers confirm all five are Accepted (`ADR-020:5-7`, `ADR-022:3-5`, `ADR-030:3`, `ADR-031:3`, `ADR-035:3-5`).
- **DOC-13 correction**: `docs/CONFIGURATION.md:314-326` lists `init`, `component list`, `component add`, `qualify`, `serve` under "Likely command surfaces may include equivalents of" and line 326 states "These commands are not implemented by this configuration slice and are not yet public CLI commitments." The deep-audit Round 2 scan called this Promise-without-Reality; it is a disclaimed forward sketch. Residual gap: the sketch omits `discover`, which is implemented (`cli.py:89-96`), so the list is stale rather than false. Downgrade GAP-DOC-13 to LOW; Sprint 1 action shrinks to adding `discover` to the sketch.
- **Verified Against Blueprint**: DRIFT against `docs/RESEARCH_BRIEF.md` (not the blueprint): DOC-13 severity.

### 6. Dependabot (GAP-CI-05)

- **Location**: `.github/` contains CODEOWNERS, ISSUE_TEMPLATE, FUNDING.yml.example, workflows, and the FailSafe-written copilot-instructions.md; no `dependabot.yml`. GitHub-side security updates are enabled (brief, CI recon).
- **Fix shape**: `version: 2` with two `updates` entries: `package-ecosystem: pip` rooted at `/reference` (requirements.txt) and `package-ecosystem: github-actions` at `/`. Both weekly. Grouping actions updates into one PR keeps the 58-workflow churn manageable. This also seeds GAP-CI-03 (SHA pinning) without performing it.
- **Verified Against Blueprint**: MATCH (governance controls).

### 7. README Conformance badge (GAP-DOC-01, badge only)

- **Location**: `README.md:18` `![Conformance](https://img.shields.io/badge/Conformance-Level%206%20Spec-7c3aed)`. Sibling badges (`:16-21`) use the pattern `<Category>-<Noun phrase>` and are unlinked except ADRs, Fixtures, License. Emitted conformance level is 0 (`reference/run_conformance.py:190`); `docs/06-conformance-test-plan.md:21` defines Level 6.
- **Fix shape**: reword to a spec-scoped phrase such as `Conformance-Levels%201--6%20Defined` and link it to `docs/06-conformance-test-plan.md`, matching how the ADRs badge links to its index. `docs/CONCEPT.md` is unchanged per owner decision.
- **Verified Against Blueprint**: MATCH.

### 8. Wheel-install CI check

- **Location**: `cli-doctor.yml:26` and `provider-discovery.yml:26` already run `python -m pip install --disable-pip-version-check .`, but from the repository root, where `receipts.py:28` resolves the source `schemas/` directory and masks the wheel defect; `cli-doctor.yml:118` additionally echoes the command into the step summary. No workflow installs a built wheel from outside the checkout. (Corrected after audit V2.)
- **Fix shape**: one job that builds a wheel (`python -m build --wheel`), installs it into a fresh venv with no repo on `sys.path` (run from `/tmp`), then executes `python -c "import agentmem_ref.receipts as r; r.validate('decision-receipt.schema.json', {...})"` is too coupled; the minimal assertion is `import agentmem_ref.receipts` plus a call that forces `_validator` to load one schema, and `agent-memory --help` exit 0. Add `timeout-minutes` and `permissions: contents: read` like the siblings.
- **Verified Against Blueprint**: DRIFT. Blueprint CLI contract has no install acceptance gate.

### Recent changes audit

No target file has changed since 2026-08-15 (`pyproject.toml` 94051a4 2026-08-15; `requirements.txt` 2ac29ef 2026-08-12; `receipts.py` 553fb1b 2026-08-12; `cedar_policy_comparator.py` 9610636 2026-08-13; `README.md` a2ecc70 2026-08-12; `docs/CONFIGURATION.md` 192a9eb 2026-08-14). Impact on the brief's citations: NONE.

## Blueprint Alignment

| Blueprint Claim | Actual Finding | Status |
|---|---|---|
| Dependencies: jsonschema is "the single runtime dependency" | 17 modules require cryptography/rfc8785 at import (`requirements.txt:4,7`) | DRIFT: amend the Dependencies table in the plan for this sprint |
| CLI contract: `agent-memory` validates, discovers, diagnoses | Correct from source; installed wheel breaks `commit_proposal`, not the CLI | MATCH (CLI); DRIFT (installed package usability) |
| Governance controls: secret scanning and branch protection | GitHub-side scanning enabled; dependabot config absent; `.gitattributes` absent | MATCH (documented as to-confirm) |
| File tree: `schemas/` at root, 58 files | Confirmed; must remain the source of truth (`validate_schemas.py:30`, 16 workflows, 17 tests bind it) | MATCH |
| RESEARCH_BRIEF GAP-DOC-13 MEDIUM | `CONFIGURATION.md:326` already disclaims; only `discover` is missing from the sketch | DRIFT: downgrade to LOW |

## Recommendations

1. **High**: implement the RT-01 hot slice with the verified `build_py` copy + `package-data` + `importlib.resources` fallback in `receipts.py`; keep `data-files` until Sprint 3 rewrites the two fallbacks; gitignore `reference/agentmem_ref/_schemas/`.
2. **High**: declare `cryptography` and `rfc8785` as hard dependencies with upper bounds matching the pins; put `agent-manifest` and `agentrust-trace` in a `comparators` extra. Update `ARCHITECTURE_PLAN.md` Dependencies table in the same change.
3. **High**: `.gitattributes` (`* text=auto eol=lf`, binary rules for PNG/SVG as needed) and EOL-normalize in `policy_sha256`. Keep the pin value.
4. **Medium**: `skipUnless(installed == pinned)` on the two pin-identity tests via a shared helper; keep behavioural tests running.
5. **Medium**: add the wheel-install job to `cli-doctor.yml` with timeout and least-privilege permissions.
6. **Medium**: `.github/dependabot.yml` for pip (`/reference`) and github-actions (`/`), weekly, grouped.
7. **Low**: seven DOC-09 edits; add `discover` to the CONFIGURATION.md sketch; reword the README Conformance badge and link it to docs/06.
8. **Deferred**: GAP-ARCH-16 issue creation crosses the Review Boundary; list in the handoff packet.

## Updated Knowledge

- `docs/RESEARCH_BRIEF.md` GAP-DOC-13: severity MEDIUM to LOW; the commands are disclaimed at `CONFIGURATION.md:326`; residual is a stale sketch missing `discover`. Recorded as a third example under Shadow Genome Failure #2 (grep-shaped over-grading).
- Packaging pattern verified for this repo shape (package under `reference/`, data at root): `build_py` override + `package-data`, prototype in session scratchpad `pkgproto`.
- The suite runs under `unittest discover` in CI; pytest is local-only, so skip guards must be `unittest` decorators.

---

_Research complete. Findings are advisory — implementation decisions remain with the Governor._
