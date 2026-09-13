# Governance Index

**Last Reviewed**: 2026-09-12  
**Evidence Boundary**: `main` `56e44d3cd3cb9c4186596f6a064dd554d14c1940`

This is the current map of Agent Memory's governance surfaces and their freshness obligations. It is intentionally **not** an exhaustive hand-maintained list of every historical sprint plan. Historical plans are evidence and remain discoverable through `docs/plan-*.md`, `docs/research-brief-*.md`, and `docs/META_LEDGER.md`; forcing each one into a current-state index created exactly the kind of drift this file is meant to prevent.

The tier model is a repository-maintenance convention. Qor-logic is development-time tooling only: it is not a runtime, build, or test dependency of Agent Memory and nothing in `reference/` imports it. The current package dependency contract lives in `pyproject.toml`.

> **Current-roadmap authority:** `.qor/roadmaps/agent-memory-1_0-completion/events.jsonl` is **not present on current `main`**. Historical ledger entries that refer to that roadmap remain valid historical evidence, but the absent path must not be used as a current work queue. Current execution state lives in `docs/BACKLOG.md`, `docs/SYSTEM_STATE.md`, and live GitHub issues/PRs.

## Tier 1 — Current Canonical State

These surfaces MUST describe current repository reality. A wrong version, stale status, or nonexistent current path is a Tier 1 drift bug.

| Artifact | Path | Current marker |
|----------|------|----------------|
| Meta Ledger | `docs/META_LEDGER.md` | Entries #1-#59; latest SESSION SEAL #58 (Sprint 4c-2 / contract 1.2.0), followed by Entry #59 amendment |
| System State | `docs/SYSTEM_STATE.md` | reconciled 2026-09-12 against `main` `56e44d3`; Python public API 1.2.0; production hardening remains open |
| Concept | `docs/CONCEPT.md` | current objective points to Backlog/System State/live issues, not the absent `.qor` roadmap |
| Backlog | `docs/BACKLOG.md` | current blocker/order: #395 -> #364 -> #363; held/integration work explicitly separated |
| Feature Index | `docs/FEATURE_INDEX.md` | 26 feature rows are verified; FX025 is intentionally reserved for the held Sprint 4b slice |
| ADR index | `docs/adr/README.md` | ADR-001 through ADR-038; 32 Accepted, 6 Proposed |
| Package contract | `pyproject.toml` | `agent-memory-reference` 0.2.0; hard deps `jsonschema`, `cryptography`, `rfc8785`; comparator pins `agent-manifest==0.11.2`, `agentrust-trace==0.9.0` |
| README | `README.md` | current maturity language explicitly separates repository validation from production-memory proof |
| Shadow Genome | `docs/SHADOW_GENOME.md` | append-only failure/lesson record; individual resolution state lives in each entry rather than a duplicated count here |
| Process Shadow Genome | `docs/PROCESS_SHADOW_GENOME.md` | append-only process events and remediation history |

`CHANGELOG.md` is absent on current `main`; release chronology must not be inferred from a nonexistent changelog.

## Tier 2 — Doctrine and Contract Authority

Stable architectural rules. Changes require explicit doctrine/contract work; current status is determined from the artifact itself, not a duplicated count here.

| Artifact family | Path |
|-----------------|------|
| Architecture decisions | `docs/adr/README.md`, `docs/adr/ADR-001*` through `ADR-038*` |
| PAMA foundation and decision table | `docs/pama/README.md`, `docs/04-governance-and-pama.md`, `docs/33-pama-decision-table.md` |
| Public API contract | `docs/44-public-api-contract.md`, `reference/agentmem_ref/api/`, `schemas/api-*.schema.json` |
| Threat/security doctrine | `docs/15-memory-threat-model.md`, `docs/19-privacy-and-sensitivity-classifier.md`, `docs/29-actor-scope-consent-and-tenancy.md`, `docs/41-memory-isolation-domains-and-governed-crossing.md` |
| Evidence and provenance doctrine | `docs/16-source-trust-and-reputation.md`, `docs/30-memory-observability-and-audit-events.md`, `docs/policies/EVIDENCE_PROMOTION.md` |
| Lifecycle / correction / deletion doctrine | `docs/02-lifecycle-state-machine.md`, `docs/17-conflict-resolution-engine.md`, `docs/28-retention-deletion-and-tombstones.md`, `docs/31-recovery-rollback-and-replay.md` |
| Schema contracts | `schemas/*.schema.json`, registry doctrine in `docs/27-schema-registry-and-type-evolution.md` |
| Project governance | `GOVERNANCE.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `.github/CODEOWNERS` |

## Tier 3 — Active Initiatives

Live until closed or explicitly parked. GitHub issue state is authoritative for whether these remain active.

| Initiative | Tracking surface | Current state |
|------------|------------------|---------------|
| Public API/adapter semantic consistency | issue #395 | open; next inconsistency target after this drift pass |
| Recall and scope authority completion | issue #364 | open; two authority legs remain after the decision-record work |
| Production state / persistence profile | issue #363 | open; blocks production-readiness claims |
| DashClaw correction discharge | issue #392 | open but blocked on rule authorship/ownership decision |
| Live DashClaw conformance | issue #361 | open |
| QOR Agent / Cloudflare proving ground | issue #332 | open |
| Governed canonical knowledge profile | issue #387 | open |
| Field efficacy benchmark | issue #388 | open |
| Governance-memory efficacy review skill | PR #389 | open; supporting tooling for #388, not field-efficacy evidence |

## Tier 4 — Active or Held Plan Artifacts

Only plans whose lifecycle is still active/held belong here. Completed plans are historical evidence and do not need a permanent live row.

| Artifact | Path | State |
|----------|------|-------|
| Sprint 4b JS PAMA plan | `docs/plan-sprint4b-js-pama.md` | **HELD** after audit veto; direct parity port would strand corrections without a discharge route |
| Sprint 4b research brief | `docs/research-brief-sprint4b-js-pama-2026-09-07.md` | supporting research for the held plan |

The implemented Sprint 1 through Sprint 4c-2 plans remain in `docs/` and are bound into the ledger. Their continued existence is historical evidence, not a claim that the work is still pending.

## Tier 5 — Reference Material

Informational and slower-drift. A factual claim in these documents must still be corrected when it materially diverges from current code, but historical measurements should be labeled rather than rewritten as if they were always current.

| Family | Path |
|--------|------|
| Numbered doctrine / architecture references | `docs/00-*.md` through `docs/44-*.md` |
| Canonical architecture synthesis | `docs/AGENTIC_MEMORY_SYSTEMS_CANONICAL_ARCHITECTURE.md` |
| Documentation map | `docs/README.md` |
| Implementation maps | `docs/05-repo-implementation-map.md`, `docs/39-implementation-ownership-map.md` |
| Profiles | `docs/profiles/` |
| Programs | `docs/programs/` |
| PRD / RFC | `docs/prd/`, `docs/rfcs/` |
| Reference runtime guide | `reference/README.md` |
| Configuration guide | `docs/CONFIGURATION.md` |
| Wiki source | `wiki-src/` |
| Research bibliography / explorations | `docs/23-research-bibliography.md`, `docs/research/`, `docs/explorations/` |

Deep-audit gap labels embedded in reference docs are historical observations unless the gap is also carried by the current backlog or an open issue. A 2026-09-01 gap label is not automatically current merely because the prose still exists.

## Tier 6 — Historical Governance Evidence

Frozen or provenance-oriented artifacts. Their job is to preserve what was decided, measured, or planned at the time, not to impersonate current status.

| Historical family | Path / source |
|-------------------|---------------|
| Genesis architecture blueprint | `docs/ARCHITECTURE_PLAN.md` |
| Deep-audit snapshot | `docs/RESEARCH_BRIEF.md` |
| Completed implementation plans | `docs/plan-*.md` except active/held Tier 4 entries |
| Completed research briefs | `docs/research-brief-*.md` except active/held Tier 4 entries |
| Audit records | `docs/audits/` |
| Generated reports | `reports/` |
| Committed provider evidence fixtures | `reference/fixtures/component-qualification/*.json` |
| Historical branch state | branches such as `feat/agent-memory-genesis`; compare for unique commits before deletion, but do not use them as current-state authority |

`docs/META_LEDGER.md` is itself Tier 1 because its chain must remain current, while the decisions it contains are historical evidence. Those two facts are not contradictory.

## Drift Contract

When reconciling current state:

1. Read `main`, the ADR index, ledger tail, open issues/PRs, and package metadata before editing status prose.
2. Do not update historical plan/research claims merely because later work changed reality; label them historical instead.
3. Do not duplicate volatile counts unless the count adds operational value. Prefer links to authoritative inventories.
4. Any current path named here must exist on `main`, or be explicitly labeled absent/held/external.
5. `SYSTEM_STATE.md`, `BACKLOG.md`, `CONCEPT.md`, and this index must agree on the active objective and blockers before a new implementation tranche begins.

## How to Add or Retire a Governance Surface

- Add a surface to the tier matching its freshness contract in the same change that makes it authoritative.
- When active work closes, move its row out of Tier 3/4; do not keep shipped work labeled pending for nostalgia's sake.
- Preserve historical evidence unless there is a separate reason to remove it.
- Refresh **Last Reviewed** and the evidence boundary whenever Tier 1 state changes materially.
