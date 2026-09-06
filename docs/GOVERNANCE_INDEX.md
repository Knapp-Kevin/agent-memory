# Governance Index

**Last Reviewed**: 2026-09-06

A single authoritative map of every governance artifact in this project, organized
into six freshness tiers with explicit drift contracts. A stale entry here is
itself a Tier 1 drift bug, so the index is self-policing.

The tier model and drift contracts come from Qor-logic, the gated prompt-logic
system used to facilitate development of this repository. Qor-logic is a
development-time governance toolkit only: it is **not** a runtime, build, or test
dependency of Agent Memory, it ships no code into this package, and nothing in
`reference/` imports it. The `agent-memory-reference` distribution depends on
`jsonschema`, `cryptography`, and `rfc8785` (plus the optional `comparators`
extra) and on nothing else. Paths of the form `qor/...` cited in governance
documents here refer to that external toolkit's own repository, not to any
directory in this one.

## Tier 1 — Canonical Source

MUST be current at every cycle close. Drift signal: wrong version / wrong state / missing recent entries.

| Artifact | Path | Freshness marker |
|----------|------|------------------|
| Meta Ledger | `docs/META_LEDGER.md` | Entries #1-#10; Sprint 1 seal Entry #8; #9 migration attestation, #10 amendment (2026-09-04). `verify-ledger` exit 0, all 10 entries OK |
| System State | `docs/SYSTEM_STATE.md` | Sprint 1 snapshot, iteration 1 |
| Concept | `docs/CONCEPT.md` | stable; hashed into genesis; owner decision: "supported runtime" is the 1.0 objective |
| Architecture Plan | `docs/ARCHITECTURE_PLAN.md` | Dependencies table and file tree synced at Sprint 1; risk grade L3 |
| Backlog | `docs/BACKLOG.md` | B1-B4 open; B5 complete |
| Feature Index | `docs/FEATURE_INDEX.md` | 11 entries, 11 verified (FX001-FX011) |
| Shadow Genome | `docs/SHADOW_GENOME.md` | 5 entries, 4 resolved |
| Process Shadow Genome | `docs/PROCESS_SHADOW_GENOME.md` | append-only JSONL of process events (capability shortfalls, gate skips, overrides) |
| Changelog | `CHANGELOG.md` | **absent** (GAP-REL-01, Sprint 8); register here when created |
| README | `README.md` | Conformance badge spec-scoped (Sprint 1); installable distribution (Loop 7); **ownership section** — contracts are Agent Memory's, implementations live here (2026-09-04) |
| Roadmap events | `.qor/roadmaps/agent-memory-1_0-completion/events.jsonl` | 32 events; 7 frontier nodes open |

## Tier 2 — Doctrine & Policy

Stable; changes are explicit doctrine events. Drift signal: rules contradict each other or operator memory.

| Artifact | Path |
|----------|------|
| ADR index (canonical status) | `docs/adr/README.md` (31 Accepted, 6 Proposed) |
| ADRs | `docs/adr/ADR-001` through `ADR-037` |
| PAMA foundation | `docs/pama/README.md`, `docs/04-governance-and-pama.md`, `docs/33-pama-decision-table.md` |
| Memory threat model | `docs/15-memory-threat-model.md` |
| Source rights policy | `docs/SOURCE_RIGHTS_POLICY.md` |
| Evidence promotion policy | `docs/policies/EVIDENCE_PROMOTION.md` |
| Project governance | `GOVERNANCE.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `.github/CODEOWNERS` |
| Schemas (contracts) | `schemas/*.schema.json` (58); registry at `docs/27-schema-registry-and-type-evolution.md` (8 listed, GAP-SC-04) |

## Tier 3 — Active Initiative

Live until close; ages out at substantiate. Drift signal: shipped feature still tracked as pending.

| Artifact | Path | Opened |
|----------|------|--------|
| Deep-audit research brief | `docs/RESEARCH_BRIEF.md` | 2026-09-01 |
| Agent Memory 1.0 roadmap | `.qor/roadmaps/agent-memory-1_0-completion/` | 2026-09-01 |
| QOR Agent proving ground | GitHub issue #332 | 2026-08-22 |
| Genesis branch | `feat/agent-memory-genesis` | 2026-09-01 |

## Tier 4 — Per-Plan Artifact

Live for plan duration; archived at substantiate. Drift signal: plan shipped but artifact still presents as open.

| Artifact | Path | Plan |
|----------|------|------|
| Sprint 1 plan (sealed) | `docs/plan-sprint1-install-correctness.md` | sprint1-install-correctness |
| Sprint 1 research brief | `docs/research-brief-sprint1-install-correctness-2026-09-01.md` | sprint1-install-correctness |
| Ledger repair plan | `docs/plan-ledger-markup-repair.md` | ledger-markup-repair |
| Ledger repair research brief | `docs/research-brief-ledger-markup-repair-2026-09-04.md` | ledger-markup-repair |
| Sprint 2a plan | `docs/plan-sprint2a-identity-and-decision-table.md` | sprint2a-identity-and-decision-table |
| Sprint 2a research brief | `docs/research-brief-sprint2a-identity-and-decision-table-2026-09-04.md` | sprint2a-identity-and-decision-table |
| Sprint 2b plan | `docs/plan-sprint2b-recall-authority-record.md` | sprint2b-recall-authority-record |
| Sprint 2b research brief | `docs/research-brief-sprint2b-recall-authority-record-2026-09-04.md` | sprint2b-recall-authority-record |
| Sprint 2c plan | `docs/plan-sprint2c-deletion-authority.md` | sprint2c-deletion-authority |
| Sprint 2c research brief | `docs/research-brief-sprint2c-deletion-authority-2026-09-04.md` | sprint2c-deletion-authority |
| Sprint 2d plan | `docs/plan-sprint2d-derived-authority.md` | sprint2d-derived-authority |
| Sprint 2d research brief | `docs/research-brief-sprint2d-derived-authority-2026-09-04.md` | sprint2d-derived-authority |
| Sprint 2e plan | `docs/plan-sprint2e-ratification-anchor.md` | sprint2e-ratification-anchor |
| Sprint 2e research brief | `docs/research-brief-sprint2e-ratification-anchor-2026-09-04.md` | sprint2e-ratification-anchor |
| Sprint 2f plan | `docs/plan-sprint2f-verified-discharge.md` | sprint2f-verified-discharge |
| Sprint 2f research brief | `docs/research-brief-sprint2f-verified-discharge-2026-09-04.md` | sprint2f-verified-discharge |
| Sprint 2g plan | `docs/plan-sprint2g-parked-verification.md` | sprint2g-parked-verification |
| Sprint 2g research brief | `docs/research-brief-sprint2g-parked-verification-2026-09-04.md` | sprint2g-parked-verification |
| Sprint 2h plan | `docs/plan-sprint2h-evidence-qualification.md` | sprint2h-evidence-qualification |
| Sprint 2h research brief | `docs/research-brief-sprint2h-evidence-qualification-2026-09-05.md` | sprint2h-evidence-qualification |
| Sprint 2i plan | `docs/plan-sprint2i-governed-resumption.md` | sprint2i-governed-resumption |
| Sprint 2i research brief | `docs/research-brief-sprint2i-governed-resumption-2026-09-05.md` | sprint2i-governed-resumption |
| Sprint 2j plan | `docs/plan-sprint2j-strength-ladder.md` | sprint2j-strength-ladder |
| Sprint 2j research brief | `docs/research-brief-sprint2j-strength-ladder-2026-09-05.md` | sprint2j-strength-ladder |
| Sprint 2k plan | `docs/plan-sprint2k-qualified-discharge.md` | sprint2k-qualified-discharge |
| Sprint 2k research brief | `docs/research-brief-sprint2k-qualified-discharge-2026-09-05.md` | sprint2k-qualified-discharge |
| Sprint 2l plan | `docs/plan-sprint2l-evidence-producers.md` | sprint2l-evidence-producers |
| Sprint 2l research brief | `docs/research-brief-sprint2l-evidence-producers-2026-09-05.md` | sprint2l-evidence-producers |
| Sprint 2m plan | `docs/plan-sprint2m-fail-closed-flip.md` | sprint2m-fail-closed-flip |
| Sprint 2m research brief | `docs/research-brief-sprint2m-fail-closed-flip-2026-09-05.md` | sprint2m-fail-closed-flip |
| Sprint 2n plan | `docs/plan-sprint2n-seal-anchors.md` | sprint2n-seal-anchors |
| Sprint 2n research brief | `docs/research-brief-sprint2n-seal-anchors-2026-09-05.md` | sprint2n-seal-anchors |
| Sprint 3b plan | `docs/plan-sprint3b-visibility-test-discover.md` | sprint3b-visibility-test-discover |
| Sprint 3b research brief | `docs/research-brief-sprint3b-visibility-test-discover-2026-09-06.md` | sprint3b-visibility-test-discover |

## Tier 5 — Reference Material

Informational, slow-drift. Drift signal: factual claims diverge from current code.

| Artifact | Path |
|----------|------|
| Doctrine 00 | `docs/00-glossary.md` |
| Doctrine 01 | `docs/01-layer-model.md` |
| Doctrine 02 | `docs/02-lifecycle-state-machine.md` |
| Doctrine 03 | `docs/03-scoring-and-decay.md` |
| Doctrine 04 | `docs/04-governance-and-pama.md` |
| Doctrine 05 | `docs/05-repo-implementation-map.md` |
| Doctrine 06 | `docs/06-conformance-test-plan.md` |
| Doctrine 07 | `docs/07-integration-roadmap.md` |
| Doctrine 08 | `docs/08-source-material-index.md` |
| Doctrine 09 | `docs/09-calibration-protocol.md` |
| Doctrine 10 | `docs/10-memory-unit-examples.md` |
| Doctrine 11 | `docs/11-component-architecture.md` |
| Doctrine 12 | `docs/12-concept-segmentation-matrix.md` |
| Doctrine 13 | `docs/13-system-composition-boundaries.md` |
| Doctrine 14 | `docs/14-expanded-scope-recommendations.md` |
| Doctrine 15 | `docs/15-memory-threat-model.md` |
| Doctrine 16 | `docs/16-source-trust-and-reputation.md` |
| Doctrine 17 | `docs/17-conflict-resolution-engine.md` |
| Doctrine 18 | `docs/18-temporal-causality-layer.md` |
| Doctrine 19 | `docs/19-privacy-and-sensitivity-classifier.md` |
| Doctrine 20 | `docs/20-memory-foundations-across-scales.md` |
| Doctrine 21 | `docs/21-forgetting-consolidation-and-memory-metabolism.md` |
| Doctrine 22 | `docs/22-agentic-memory-theory-and-development.md` |
| Doctrine 23 | `docs/23-research-bibliography.md` |
| Doctrine 24 | `docs/24-determinism-probability-and-governed-uncertainty.md` |
| Doctrine 25 | `docs/25-governed-uncertainty-documentation-conformance-audit.md` |
| Doctrine 26 | `docs/26-governed-recall-planner.md` |
| Doctrine 27 | `docs/27-schema-registry-and-type-evolution.md` |
| Doctrine 28 | `docs/28-retention-deletion-and-tombstones.md` |
| Doctrine 29 | `docs/29-actor-scope-consent-and-tenancy.md` |
| Doctrine 30 | `docs/30-memory-observability-and-audit-events.md` |
| Doctrine 31 | `docs/31-recovery-rollback-and-replay.md` |
| Doctrine 32 | `docs/32-memory-quality-metrics.md` |
| Doctrine 33 | `docs/33-pama-decision-table.md` |
| Doctrine 34 | `docs/34-adapter-contracts.md` |
| Doctrine 35 | `docs/35-interoperability-profiles.md` |
| Doctrine 36 | `docs/36-policy-as-memory.md` |
| Doctrine 37 | `docs/37-memory-economics-and-budget-policy.md` |
| Doctrine 38 | `docs/38-human-correction-ux-contract.md` |
| Doctrine 39 | `docs/39-implementation-ownership-map.md` |
| Doctrine 40 | `docs/40-aligned-projects-and-intellectual-lineage.md` |
| Doctrine 41 | `docs/41-memory-isolation-domains-and-governed-crossing.md` |
| Doctrine 42 | `docs/42-governed-mutable-memory-fabric.md` |
| Doctrine 43 | `docs/43-substrate-inventory-and-maturity.md` |
| Canonical architecture synthesis | `docs/AGENTIC_MEMORY_SYSTEMS_CANONICAL_ARCHITECTURE.md` |
| Documentation map | `docs/README.md` (reachability gaps: GAP-DOC-04) |
| Implementation maps | `docs/05-repo-implementation-map.md`, `docs/39-implementation-ownership-map.md` (stale: GAP-DOC-05) |
| Profiles | `docs/profiles/` (29) |
| Programs | `docs/programs/` (runtime-evidence, memory-modules, hermes-integration, atlas-research) |
| PRD / RFC | `docs/prd/PRD-001`, `docs/rfcs/RFC-001` (gates stale: GAP-DOC-07) |
| Reference runtime README | `reference/README.md` (41 modules undocumented: GAP-DOC-03) |
| Configuration guide | `docs/CONFIGURATION.md` (phantom CLI subcommands: GAP-DOC-13) |
| Wiki source | `wiki-src/` (two weeks behind: GAP-DOC-06) |
| Research bibliography and explorations | `docs/23-research-bibliography.md`, `docs/research/`, `docs/explorations/` |

## Tier 6 — Archived

Frozen historical record. Drift signal: none (frozen).

| Archive | Path |
|---------|------|
| Audit records | `docs/audits/` (isolation, temporal-commitments) |
| Generated reports | `reports/` |
| Committed provider evidence fixtures | `reference/fixtures/component-qualification/*.json` |

## How to add a governance artifact

1. Create the file in the same commit that registers it here.
2. Add a row to the tier whose freshness contract matches the file's lifecycle.
3. Refresh **Last Reviewed** above.

## How to retire a governance artifact

1. Move the file to the Tier 6 archive path.
2. Move its row from its live tier to Tier 6 (or delete it if superseded).
3. Refresh **Last Reviewed** above.
