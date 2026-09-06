# System State

## Snapshot Metadata

| Attribute | Value |
|-----------|-------|
| **Last Updated** | 2026-09-05T12:30:00-04:00 |
| **Updated By** | Judge |
| **Phase** | SUBSTANTIATED (Sprint 2n seal anchors -- ledger Merkle seals durable and remotely verifiable) |
| **Iteration** | 15 |
| **Session Seal** | Entry #25 (session 2026-09-05T1100-c2c873) |

Snapshot refreshed at the Sprint 2n seal (Loop 15). Every SESSION SEAL is now anchored under `refs/seals/` and verifiable from origin. ADR-037 is now enforced rather than described: assertion no longer discharges require_review anywhere. Genesis values came from the `/qor-deep-audit` reconnaissance (see `docs/RESEARCH_BRIEF.md`); deltas through Loops 2-8 are measured from the sealed tree, with the suite run under the pinned `cryptography==50.0.1` the repo declares -- not the ambient interpreter.

---

## File Tree (Current Reality)

```
agent-memory/
|-- .agent/staging/            (gitignored)
|-- .qor/
|   |-- gates/                 (gitignored session state)
|   |-- session/               (gitignored)
|   `-- roadmaps/agent-memory-1_0-completion/events.jsonl   (committed)
|-- docs/                      218 markdown files: 43 numbered doctrine docs, 35 ADRs, pama/, profiles/ (29), programs/, prd/, rfcs/, policies/, audits/, explorations/, research/, ecosystem/, templates/, future/
|   |-- CONCEPT.md, ARCHITECTURE_PLAN.md, META_LEDGER.md, BACKLOG.md, FEATURE_INDEX.md
|   |-- SYSTEM_STATE.md (this file), SHADOW_GENOME.md, GOVERNANCE_INDEX.md
|   `-- RESEARCH_BRIEF.md      deep-audit gap inventory
|-- schemas/                   58 JSON Schemas (draft 2020-12)
|-- fixtures/                  64 validated scenario fixtures
|-- reference/
|   |-- agentmem_ref/          121 modules (reference runtime + CLI)
|   |-- run_*.py               68 evidence emitters
|   |-- native/                1 Rust driver
|   |-- policies/, fixtures/ (15 JSON), testdata/
|   `-- tests/                 139 test files, 1113 tests
|-- integrations/
|   |-- agent-memory-runtime/  JS, 1 source + 1 test, private
|   `-- hermes-agent-memory/   Python, 10 modules, 6 tests
|-- scripts/                   12 repository validators
|-- wiki-src/                  27 wiki pages
|-- .github/workflows/         58 workflows (umbrella: validate-doctrine-evidence.yml)
`-- pyproject.toml             agent-memory-reference 0.1.0, console script agent-memory
```

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Source Files | 121 (`reference/agentmem_ref`) + 68 emitters + 12 scripts + 11 integration modules |
| Total Test Files | 137 (`reference/tests`) + 6 (hermes) + 1 (JS) |
| Total Lines of Code | 60,376 under `reference/` |
| Average File Size | ~300 lines (`agentmem_ref`) |
| Max File Size | 733 lines (file: `reference/agentmem_ref/runtime_config.py`) |
| Max Function Size | 311 lines (file: `reference/agentmem_ref/precedent_candidate_harness.py:177`) |
| Section 4 Violations | 58 files >250 lines; 175 functions >40 lines; 22 functions nesting >3 (if/for/while/with/try metric) |

---

## Blueprint Compliance

Compared `docs/ARCHITECTURE_PLAN.md` file tree (Promise) against the working tree (Reality) at genesis.

| Status | Planned | Actual | Notes |
|--------|---------|--------|-------|
| OK Delivered | 16 top-level paths | 16 | Every directory in the blueprint tree exists |
| WARN Unplanned | 0 | 3 | `docs/SYSTEM_STATE.md`, `docs/SHADOW_GENOME.md`, `docs/GOVERNANCE_INDEX.md` seeded by governance scaffold after the blueprint was hashed; `docs/RESEARCH_BRIEF.md` is an audit artifact |
| FAIL Missing | 0 | 0 | none |

**Compliance Rate**: 100% (blueprint is descriptive of an existing repo; forward scope is roadmap-owned)

---

## Dependency Manifest

| Package | Approved | Installed | Status |
|---------|----------|-----------|--------|
| jsonschema >=4.20,<5 | OK | OK (4.26.0 pinned in requirements) | OK |
| cryptography 50.0.0 | FAIL (not in pyproject) | OK (requirements only) | UNPLANNED (GAP-ARCH-03) |
| rfc8785 0.1.4 | FAIL (not in pyproject) | OK (requirements only) | UNPLANNED (GAP-ARCH-03) |
| agent-manifest 0.11.0 | FAIL (not in pyproject) | OK (requirements; comparator-only) | UNPLANNED (GAP-ARCH-03) |
| agentrust-trace 0.8.0 | FAIL (not in pyproject) | OK (requirements; comparator-only) | UNPLANNED (GAP-ARCH-03) |
| graphiti-core, kuzu | FAIL | FAIL (CI-only, unpinned) | MISSING for the only non-toy substrate (GAP-ARCH-02, GAP-DOC-02) |

---

## Section 4 Razor Compliance

### File-Level (Macro KISS)

| File | Lines | Status |
|------|-------|--------|
| `reference/agentmem_ref/runtime_config.py` | 733/250 | FAIL |
| `reference/agentmem_ref/capabilities.py` | 726/250 | FAIL |
| `reference/agentmem_ref/cedar_policy_comparator.py` | 626/250 | FAIL |
| `reference/agentmem_ref/procedural_memory.py` | 601/250 | FAIL |
| `reference/agentmem_ref/dashclaw_external_verdict.py` | 595/250 | FAIL |
| 53 further modules | >250 | FAIL (tracked as GAP-RT-04, Sprint 11) |
| `scripts/validate_fixtures.py`, `validate_schemas.py`, `generate_calibration_report.py`, `build_atlas_research_inventory.py` | 276-347/250 | FAIL |

### Function-Level (Micro KISS)

| File | Longest Function | Deepest Nesting | Status |
|------|-----------------|-----------------|--------|
| `reference/agentmem_ref/precedent_candidate_harness.py` | 311/40 lines | - | FAIL |
| `reference/agentmem_ref/runtime_config.py` | 249/40 lines (`validate_runtime_configuration`) | - | FAIL |
| `reference/agentmem_ref/doctor.py` | 117/40 lines (`diagnose`) | 5/3 levels | FAIL |
| `reference/agentmem_ref/approval_evidence.py` | - | 8/3 levels | FAIL |
| `reference/agentmem_ref/portable_evidence.py` | - | 8/3 levels | FAIL |

Pre-existing at genesis. Any new file under `/qor-plan` must meet the razor.

---

## Test Coverage

| Component | Test File | Exists | Passing |
|-----------|-----------|--------|---------|
| Reference runtime (all) | `reference/tests/` (137 files) | OK | 1109 pass / 0 fail / 7 skip under pinned `cryptography==50.0.1`; CI green on `main` |
| Cedar digest pin | `reference/tests/test_cedar_policy_comparator.py:71` | OK | FAIL on Windows checkouts (GAP-RT-02) |
| Third-party version pins | `test_agent_manifest_correlation.py:151`, `test_trace_action_evidence.py:118` | OK | FAIL unless env matches requirements (GAP-RT-03) |
| Graphiti substrate | `reference/tests/test_graphiti_substrate.py` | OK | SKIPPED (7) without graphiti/kuzu (GAP-RT-07) |
| CLI / doctor | `reference/tests/test_cli_doctor.py`, `test_provider_discovery.py` | OK | OK |
| 8 modules without a unit test | see GAP-RT-09 | FAIL | - |
| Hermes integration | `integrations/hermes-agent-memory/tests/` (6) | OK | OK (PR-scoped CI) |
| JS runtime adapter | `integrations/agent-memory-runtime/test/` (1) | OK | OK (PR-scoped CI) |

---

## Recent Changes

Sprint 1 install correctness (branch `feat/agent-memory-genesis`, staged, uncommitted; genesis DNA also staged):

| File | Change Type | Lines Changed |
|------|-------------|---------------|
| `setup.py`, `MANIFEST.in`, `.gitattributes`, `.github/dependabot.yml` | Created | +29, +1, +7, +13 |
| `pyproject.toml` | Modified | deps (cryptography, rfc8785), `comparators` extra, package-data |
| `reference/agentmem_ref/receipts.py` | Modified | `_SOURCE_SCHEMAS`, `_packaged_schemas`, `schema_dir`; `_validator` reads through it |
| `reference/agentmem_ref/cedar_policy_comparator.py` | Modified | `policy_sha256` normalizes CRLF |
| `reference/tests/{pin_support,test_pin_support,test_receipts_schema_location}.py` | Created | +16, +23, +55 |
| `reference/tests/{test_cedar_policy_comparator,test_agent_manifest_correlation,test_trace_action_evidence}.py` | Modified | EOL test; two `skipUnless` pin guards |
| `.github/workflows/cli-doctor.yml` | Modified | `wheel-install` job (+38) |
| `README.md`, `docs/CONFIGURATION.md`, 6 doc/wiki files | Modified | badge; `discover`; nine stale-status replacements |
| `docs/ARCHITECTURE_PLAN.md`, `docs/FEATURE_INDEX.md`, `docs/RESEARCH_BRIEF.md`, `docs/GOVERNANCE_INDEX.md` | Modified | deps table + file tree; FX001-FX003; GAP-DOC-09/13; tiers refreshed |
| `.gitignore` | Modified | `_schemas/`, tooling state; LF-normalized |

---

## Health Indicators

| Indicator | Status | Details |
|-----------|--------|---------|
| Merkle Chain | VALID | Entries #1-#8; Entry #6 hashes recomputed once for a verdict-line format fix (recorded in-entry) |
| Blueprint Sync | SYNCED | File tree and Dependencies table updated at Sprint 1 |
| Section 4 Compliance | VIOLATIONS (pre-existing) | New code clean; 58 file + 175 function pre-existing overages (GAP-RT-04, Sprint 11) |
| Test Status | PASS | 1109 run, 0 fail, 7 skipped (Graphiti/kuzu absent) under the pinned `cryptography==50.0.1`; fresh-venv wheel smoke exit 0 |

---

## Next Actions

Based on current state:

- [ ] Operator: review the Review Boundary handoff packet, commit the genesis + Sprint 1 change set on `feat/agent-memory-genesis`, decide push/PR
- [ ] Operator (Sprint 0 decisions still open): GAP-XW-01, GAP-XW-02, GAP-SEC-01 ruleset
- [ ] Loop 2: `/qor-research` then `/qor-plan` for Sprint 2 authority-path hardening (host authenticates recall principals, additive path)
- [ ] Sprint 3 (wheel-safe remainder) may run in parallel with Sprint 2

---

*State snapshot updated by Qor-logic A.E.G.I.S.*
*Run `/qor-status` for live diagnostic.*
