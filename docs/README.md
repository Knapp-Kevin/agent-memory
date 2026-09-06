# Agent Memory Documentation

<p align="center">
  <img src="../assets/brand/agent-memory-mark.png" alt="Agent Memory emblem: layered memory stack with connected nodes, an orbit, and a cyan inference spark." width="140">
</p>

This directory is the canonical documentation map for the Agent Memory reference architecture.

The repository is intentionally layered. Start with the smallest path that answers your question, then follow links deeper. Reading all forty-two numbered documents in numerical order is legal, but there are more humane options.

## Choose your path

| Reader | Start here | Then continue to |
|---|---|---|
| Researcher / theorist | [`20-memory-foundations-across-scales.md`](20-memory-foundations-across-scales.md) | `21`, `23`, `24` |
| Agent architect | [`01-layer-model.md`](01-layer-model.md) | `11`, `13`, `22`, `24`, `41`, `42` |
| Implementer | [`22-agentic-memory-theory-and-development.md`](22-agentic-memory-theory-and-development.md) | `02`-`10`, `26`-`42`, schemas and fixtures |
| Governance / adaptive-authority architect | [`pama/README.md`](pama/README.md) | `04`, `17`, `33`, `34`, ADR-004, ADR-020, ADR-022, ADR-024, ADR-032 |
| Governance integration architect | [`profiles/governance-context-projection-profile.md`](profiles/governance-context-projection-profile.md) | `11`, `34`, `42`, ADR-021, ADR-028, ADR-029, `07` roadmap |
| Security / privacy reviewer | [`15-memory-threat-model.md`](15-memory-threat-model.md) | `16`, `19`, `28`, `29`, `41` |
| Evaluator / governance reviewer | [`06-conformance-test-plan.md`](06-conformance-test-plan.md) | `09`, `24`, `25`, audit records |
| Source / provenance reviewer | [`08-source-material-index.md`](08-source-material-index.md) | [`40-aligned-projects-and-intellectual-lineage.md`](40-aligned-projects-and-intellectual-lineage.md), [`SOURCE_RIGHTS_POLICY.md`](SOURCE_RIGHTS_POLICY.md), external source registry, `23` |
| Product / UX designer | [`11-component-architecture.md`](11-component-architecture.md) | `19`, `22`, `26`, `38`, `42`, [`prd/`](prd/) |
| ADR reviewer | [`adr/README.md`](adr/README.md) | ADR-001 through ADR-032 |

## Native PAMA doctrine

**Proportional Adaptive Mutation Authority (PAMA)** is native Agent Memory doctrine authored by **Kevin R. Knapp**.

Start with [`pama/README.md`](pama/README.md) for the systems-agnostic foundation:

- adaptation is not authority
- memory is not procedure
- procedure is not permission
- permission is not governance
- M0-M5 mutation target classes
- lifecycle strength
- A0-A5 downstream authority classes
- proportional handling lanes
- adaptive charters
- capability authority ceilings

Then use [`04-governance-and-pama.md`](04-governance-and-pama.md) and [`33-pama-decision-table.md`](33-pama-decision-table.md) for the Agent Memory specialization.

PAMA is not represented as an external source dependency. External research, standards, and implementations that support or challenge PAMA retain separate provenance and source-rights treatment.

## 00-10: Canonical architecture spine

| # | Document | Purpose |
|---|---|---|
| 00 | [`00-glossary.md`](00-glossary.md) | Canonical vocabulary and term boundaries |
| 01 | [`01-layer-model.md`](01-layer-model.md) | Layer ownership, deterministic substrate, probabilistic epistemics, governance boundaries |
| 02 | [`02-lifecycle-state-machine.md`](02-lifecycle-state-machine.md) | Memory states, proposal-versus-commit, promotion, dispute, correction, pruning |
| 03 | [`03-scoring-and-decay.md`](03-scoring-and-decay.md) | Saturation, decay, uncertainty, calibration, drift, threshold stability |
| 04 | [`04-governance-and-pama.md`](04-governance-and-pama.md) | Native PAMA specialization: mutation authority and bounded consequence |
| 05 | [`05-repo-implementation-map.md`](05-repo-implementation-map.md) | Mapping of related implementations into the architecture while keeping native doctrine separate |
| 06 | [`06-conformance-test-plan.md`](06-conformance-test-plan.md) | Conformance Levels 0-6 and adversarial fixture requirements |
| 07 | [`07-integration-roadmap.md`](07-integration-roadmap.md) | Doctrine-to-implementation roadmap, including the Governance Projection track |
| 08 | [`08-source-material-index.md`](08-source-material-index.md) | External/related provenance, public source locators, rights posture, and evidence domains |
| 09 | [`09-calibration-protocol.md`](09-calibration-protocol.md) | Calibration, abstention, hysteresis, disagreement, drift |
| 10 | [`10-memory-unit-examples.md`](10-memory-unit-examples.md) | Concrete memory, uncertainty, authority, receipt, and scope examples |

### Source rights, provenance, and aligned projects

- [`40-aligned-projects-and-intellectual-lineage.md`](40-aligned-projects-and-intellectual-lineage.md) defines how Agent Memory celebrates external developers and projects without implying dependency, endorsement, joint authorship, or license transfer. Current highlighted governance peers include DashClaw and Microsoft Agent Governance Toolkit under explicit independence boundaries.
- [`SOURCE_RIGHTS_POLICY.md`](SOURCE_RIGHTS_POLICY.md) defines citation, synthesis, author-originated, licensed, and permission-based reuse modes.
- [`../sources/source-registry.json`](../sources/source-registry.json) records external/private/material-reuse source posture.
- [`../schemas/source-record.schema.json`](../schemas/source-record.schema.json) makes those source-rights records machine-checkable.

The default for external sources is citation plus independent synthesis. Public readability is not treated as an open license, and private canonical provenance is not replaced with convenient but inaccurate public substitutes.

Native contributor-authored doctrine does not need to masquerade as an external source. Its authorship and canonical location belong in the doctrine tree.

## 11-19: Composition, security, trust, time, and privacy

| # | Document | Purpose |
|---|---|---|
| 11 | [`11-component-architecture.md`](11-component-architecture.md) | Component boundaries and control character, including Governance Context Projection |
| 12 | [`12-concept-segmentation-matrix.md`](12-concept-segmentation-matrix.md) | Where concepts belong and when they deserve promotion into doctrine |
| 13 | [`13-system-composition-boundaries.md`](13-system-composition-boundaries.md) | Typed handoffs and composition-specific failure modes |
| 14 | [`14-expanded-scope-recommendations.md`](14-expanded-scope-recommendations.md) | Controlled architecture expansion candidates |
| 15 | [`15-memory-threat-model.md`](15-memory-threat-model.md) | Poisoning, leakage, authority laundering, deletion residue, composition attacks |
| 16 | [`16-source-trust-and-reputation.md`](16-source-trust-and-reputation.md) | Source trust, independence, latent preference, reputation scope |
| 17 | [`17-conflict-resolution-engine.md`](17-conflict-resolution-engine.md) | Conflict interpretation, pre-write shared-mutation coordination, and governed resolution consequences |
| 18 | [`18-temporal-causality-layer.md`](18-temporal-causality-layer.md) | Event time, valid time, supersession, causal uncertainty, prospective memory |
| 19 | [`19-privacy-and-sensitivity-classifier.md`](19-privacy-and-sensitivity-classifier.md) | Sensitivity, recall privacy, minimization, composition leakage, deletion fidelity |

## 20-25: Interdisciplinary theory and governed uncertainty

| # | Document | Purpose |
|---|---|---|
| 20 | [`20-memory-foundations-across-scales.md`](20-memory-foundations-across-scales.md) | Biological, cognitive, agentic, collective, inherited, and evolutionary-scale memory |
| 21 | [`21-forgetting-consolidation-and-memory-metabolism.md`](21-forgetting-consolidation-and-memory-metabolism.md) | Forgetting, consolidation, semanticization, deletion, and memory metabolism |
| 22 | [`22-agentic-memory-theory-and-development.md`](22-agentic-memory-theory-and-development.md) | Engineering doctrine, memory functions, write/read paths, development sequence |
| 23 | [`23-research-bibliography.md`](23-research-bibliography.md) | Dated evidence map across memory science and agent-memory research |
| 24 | [`24-determinism-probability-and-governed-uncertainty.md`](24-determinism-probability-and-governed-uncertainty.md) | Deterministic substrate, probabilistic epistemics, bounded authority, doctrine challenges |
| 25 | [`25-governed-uncertainty-documentation-conformance-audit.md`](25-governed-uncertainty-documentation-conformance-audit.md) | GU-1 through GU-10 documentation-conformance rubric |

## 26-42: Executable, operational, ecosystem, isolation, and mutable-fabric contracts

| # | Document | Purpose |
|---|---|---|
| 26 | [`26-governed-recall-planner.md`](26-governed-recall-planner.md) | Candidate retrieval versus governed context admission |
| 27 | [`27-schema-registry-and-type-evolution.md`](27-schema-registry-and-type-evolution.md) | Semantic schema compatibility and type evolution |
| 28 | [`28-retention-deletion-and-tombstones.md`](28-retention-deletion-and-tombstones.md) | Forgetting modes, deletion propagation, tombstones, verification |
| 29 | [`29-actor-scope-consent-and-tenancy.md`](29-actor-scope-consent-and-tenancy.md) | Principals, delegation, consent, purpose, tenancy, sharing scope |
| 30 | [`30-memory-observability-and-audit-events.md`](30-memory-observability-and-audit-events.md) | Structured memory events and reconstruction evidence |
| 31 | [`31-recovery-rollback-and-replay.md`](31-recovery-rollback-and-replay.md) | Recovery, compensation, state/version binding, replay semantics |
| 32 | [`32-memory-quality-metrics.md`](32-memory-quality-metrics.md) | Ongoing quality, safety, calibration, deletion, and outcome metrics |
| 33 | [`33-pama-decision-table.md`](33-pama-decision-table.md) | Agent Memory operation/risk policy projection of native PAMA doctrine |
| 34 | [`34-adapter-contracts.md`](34-adapter-contracts.md) | Typed seam contracts, including the governance-context projection adapter boundary |
| 35 | [`35-interoperability-profiles.md`](35-interoperability-profiles.md) | Six cumulative reliance profiles for cross-system memory exchange |
| 36 | [`36-policy-as-memory.md`](36-policy-as-memory.md) | Policies as high-authority memory: versioning, certification, conflict, complete recall |
| 37 | [`37-memory-economics-and-budget-policy.md`](37-memory-economics-and-budget-policy.md) | Budget dimensions and the pressure-shapes-priority-never-authority boundary |
| 38 | [`38-human-correction-ux-contract.md`](38-human-correction-ux-contract.md) | Minimum user-facing evidence, correction, dispute, and indicator contract |
| 39 | [`39-implementation-ownership-map.md`](39-implementation-ownership-map.md) | Doctrine ownership versus candidate runtime implementation ownership |
| 40 | [`40-aligned-projects-and-intellectual-lineage.md`](40-aligned-projects-and-intellectual-lineage.md) | Relationship-typed recognition, licensing boundaries, and visible credit for aligned external work |
| 41 | [`41-memory-isolation-domains-and-governed-crossing.md`](41-memory-isolation-domains-and-governed-crossing.md) | Logical isolation domains, same-agent task/project separation, governed crossings, shared-memory domains, and derived-scope inheritance |
| 42 | [`42-governed-mutable-memory-fabric.md`](42-governed-mutable-memory-fabric.md) | Agent Runtime / Agent Memory / Agent Governance boundary, configurable memory modules, routing, and governed structural mutability |
| 43 | [`43-substrate-inventory-and-maturity.md`](43-substrate-inventory-and-maturity.md) | Which substrates exist and where, their maturity, qualified external components, and which named concepts (Code Reality Graph, GraphRAG, Markdown, Postgres) are roles or mechanisms rather than substrates |

## Profiles and future subsystems

| Document | Purpose |
|---|---|
| [`profiles/durable-decision-memory-profile.md`](profiles/durable-decision-memory-profile.md) | Decision memory: required fields, rationale preservation, supersession, drift, recall |
| [`profiles/governance-context-projection-profile.md`](profiles/governance-context-projection-profile.md) | Vendor-neutral derived precedent/context for external governance consumers without exporting final authority |
| [`future/memory-compiler.md`](future/memory-compiler.md) | Bulk artifact-to-memory-unit conversion at scale, gated future subsystem |
| [`future/multi-agent-shared-memory-protocol.md`](future/multi-agent-shared-memory-protocol.md) | Shared memory across agents and tenants, gated future subsystem |

## RFCs and product requirements

RFCs define implementation-facing architecture proposals without replacing canonical ADR doctrine. PRDs translate doctrine and RFC shape into product requirements and acceptance gates.

| Collection | Start here | Current focus |
|---|---|---|
| RFCs | [`rfcs/README.md`](rfcs/README.md) | RFC-001 governed mutable memory fabric |
| PRDs | [`prd/README.md`](prd/README.md) | PRD-001 configurable Agent Memory runtime |

## Programs

Programs hold multi-slice work that produces evidence rather than doctrine. They use grouped paths instead of extending the canonical numbering.

| Program | Purpose |
|---|---|
| [`programs/runtime-evidence/README.md`](programs/runtime-evidence/README.md) | Moving from doctrine-validated to implementation-evidenced: substrate mapping, adapters, benchmarks, and the ADR-020 evidence path |

## Architecture Decision Records

See [`adr/README.md`](adr/README.md).

The ADR index is the canonical hand-maintained doctrine-status ledger. This documentation map deliberately does not duplicate the complete status table, because duplicated current-state ledgers drift.

Current decision highlights relevant to the documentation map:

- **ADR-020** is Accepted after its explicitly stronger executable governed-uncertainty evidence gate.
- **ADR-022** is Accepted for logical memory isolation domains and governed boundary crossing.
- **ADR-024** is Accepted for pre-write coordination of shared durable-memory mutation.
- **ADR-028** is Accepted and preserves a language-neutral normative core with optional implementation/interoperability profiles.
- **ADR-030** is Accepted and requires versioned compatibility/currentness before memory-derived projections are treated as current temporal or authorization input.
- **ADR-031** is Accepted and binds material temporal claims into deterministic commitments while keeping signer trust, external witness evidence, lifecycle currentness, and PAMA authority separate.
- **ADR-032** is Accepted and permits structural adaptation while requiring canonical structural-mutation authority to be deterministic and versioned or explicitly human-authorized.
- **ADR-021, ADR-023, ADR-025, ADR-026, ADR-027, and ADR-029** remain Proposed unless and until their individual maturity reviews change the canonical ADR status. Merged implementation evidence does not silently promote doctrine.

## Governance Context Projection

Proposed [`ADR-029`](adr/ADR-029-governance-projection-is-derived-context-not-authority.md) establishes:

```text
Agent Memory core
        |
        v
Governance Context Projection
  vendor-neutral remembered context
        |
        v
consumer-specific adapter
        |
        v
external policy / approval / enforcement runtime
```

The projection may preserve precedent, material conditions, scope, validity, provenance, negative outcomes, and derivation metadata. It does not own a final external-governance verdict, standing permission, or vendor risk score.

ADR-029 complements [`ADR-028`](adr/ADR-028-language-neutral-core-and-optional-implementation-profiles.md): the core remains language-neutral, the governance projection remains vendor-neutral, and concrete consumer integrations remain optional profiles/adapters rather than normative dependencies.

The first contract lives in [`profiles/governance-context-projection-profile.md`](profiles/governance-context-projection-profile.md) and [`../schemas/governance-context-projection.schema.json`](../schemas/governance-context-projection.schema.json). The implementation track is in [`07-integration-roadmap.md`](07-integration-roadmap.md).

## Governed mutable memory fabric

Accepted [`ADR-032`](adr/ADR-032-governed-mutable-memory-structure.md) and [`42-governed-mutable-memory-fabric.md`](42-governed-mutable-memory-fabric.md) establish:

```text
Agent Runtime
  -> Agent Memory governed fabric
       -> configurable memory modules / substrates
       -> memory-specific authority / lifecycle / admission
  -> peer Agent Governance systems through adapters
```

Memory technologies may be selected and composed per deployment or memory characteristics. Backend shape, learned representations, graph reachability, and retrieval scores do not become Agent Memory authority. Structural discovery may be probabilistic; canonical structural consequence requires a deterministic authorized envelope or explicit human authority.

Implementation design is tracked in [`rfcs/RFC-001-governed-mutable-memory-fabric.md`](rfcs/RFC-001-governed-mutable-memory-fabric.md) and [`prd/PRD-001-configurable-agent-memory-runtime.md`](prd/PRD-001-configurable-agent-memory-runtime.md).

## Governed-uncertainty audit trail

The repository preserves baseline and post-remediation evidence rather than overwriting history with the pleasant fiction that the doctrine was always this coherent.

Audit records live in [`audits/governed-uncertainty/`](audits/governed-uncertainty/).

Start with:

- [`25-governed-uncertainty-documentation-conformance-audit.md`](25-governed-uncertainty-documentation-conformance-audit.md)
- [`audits/governed-uncertainty/02-implementation-and-conformance.md`](audits/governed-uncertainty/02-implementation-and-conformance.md)
- [`audits/governed-uncertainty/03-component-composition.md`](audits/governed-uncertainty/03-component-composition.md)
- [`audits/governed-uncertainty/04-threat-trust-conflict-causality-privacy.md`](audits/governed-uncertainty/04-threat-trust-conflict-causality-privacy.md)
- [`audits/governed-uncertainty/05-interdisciplinary-theory.md`](audits/governed-uncertainty/05-interdisciplinary-theory.md)
- [`audits/governed-uncertainty/06-adr-status-and-alignment.md`](audits/governed-uncertainty/06-adr-status-and-alignment.md)
- [`audits/governed-uncertainty/07b-machine-readable-evidence.md`](audits/governed-uncertainty/07b-machine-readable-evidence.md)
- [`audits/governed-uncertainty/07c-adr-evidence-acceptance.md`](audits/governed-uncertainty/07c-adr-evidence-acceptance.md)

Source-rights and provenance audits:

- [`audits/source-rights/01-public-provenance-and-reuse-rights.md`](audits/source-rights/01-public-provenance-and-reuse-rights.md)
- [`audits/source-rights/02-pama-native-provenance-and-implementation-reference-cleanup.md`](audits/source-rights/02-pama-native-provenance-and-implementation-reference-cleanup.md)

## Machine-readable evidence

Schemas:

- [`../schemas/memory-unit.schema.json`](../schemas/memory-unit.schema.json)
- [`../schemas/conformance-report.schema.json`](../schemas/conformance-report.schema.json)
- [`../schemas/decision-receipt.schema.json`](../schemas/decision-receipt.schema.json)
- [`../schemas/boundary-crossing-receipt.schema.json`](../schemas/boundary-crossing-receipt.schema.json)
- [`../schemas/memory-audit-event.schema.json`](../schemas/memory-audit-event.schema.json)
- [`../schemas/calibration-results.schema.json`](../schemas/calibration-results.schema.json)
- [`../schemas/source-record.schema.json`](../schemas/source-record.schema.json)
- [`../schemas/pama-decision.schema.json`](../schemas/pama-decision.schema.json)
- [`../schemas/governance-context-projection.schema.json`](../schemas/governance-context-projection.schema.json)

External/material source provenance and rights records:

- [`../sources/source-registry.json`](../sources/source-registry.json)

Conformance fixtures:

- [`../fixtures/`](../fixtures/)

Validation from the repository root:

```bash
python -m pip install -r reference/requirements.txt
python scripts/validate_fixtures.py fixtures
python scripts/validate_schemas.py
python scripts/validate_doctrine_boundaries.py
python scripts/validate_wiki_links.py wiki-src
```

Repository CI runs the same validation through [`../.github/workflows/validate-doctrine-evidence.yml`](../.github/workflows/validate-doctrine-evidence.yml).

## Evidence posture

Research may support, challenge, narrow, or reject an architectural idea.

Prefer freely inspectable research where practical, but do not let accessibility outrank evidence quality. Biological and cognitive research should be classified as native mechanism, functional analogy, engineering prescription, or open hypothesis before it is transferred into software doctrine.

Evidence availability and reuse permission remain separate questions. External research sources are citation/synthesis-only by default unless material reuse has an explicit rights record.

The repository's job is not to collect citations until an idea looks inevitable. Its job is to make assumptions inspectable enough that good evidence can change them without making the repository a rights-management guessing game.
