# Architecture Plan

Genesis blueprint for an existing, mature repository. This plan records the contract as it stands at genesis and the forward scope toward Agent Memory 1.0. It does not re-plan delivered work; feature-level work enters through `/qor-plan`.

## Risk Grade: L3

### Risk Assessment
- [x] Contains security/auth logic -> L3 (PAMA mutation authority, approval verification, source trust, privacy/sensitivity classification, isolation-domain crossing, retention/deletion)
- [x] Modifies existing APIs -> L2 (runtime API boundary and package surface are in forward scope)
- [ ] UI-only changes -> L1

L3 is mandatory: the core thesis is that authority constrains consequence. Any error in the authority path is a security failure by definition.

## File Tree (The Contract)

```
agent-memory/
|-- docs/                     Canonical doctrine (42 numbered docs), ADRs (36), PAMA, profiles, policies, PRDs, RFCs
|   |-- adr/                  Architecture decision index; Accepted/Proposed/Superseded status lives here only
|   |-- pama/                 Proportional Adaptive Mutation Authority foundation
|   |-- CONCEPT.md            Qor-logic Why / Vibe / Anti-Goals (this genesis)
|   |-- ARCHITECTURE_PLAN.md  This file
|   |-- META_LEDGER.md        Merkle-chain decision ledger
|   |-- BACKLOG.md            Blockers / backlog / wishlist
|   `-- FEATURE_INDEX.md      Feature-to-doc/code/test cross-reference
|-- schemas/                  58 JSON Schemas: memory units, runtime configuration, provider probes, contracts
|-- fixtures/                 Validated corpus consumed by conformance and evidence workflows
|-- reference/
|   |-- agentmem_ref/         Reference runtime + diagnostic CLI (package agent-memory-reference, entry point agent-memory)
|   |-- native/               First-party substrate implementations (epistemic, predictive, procedural, reality graph, metabolism)
|   |-- policies/             Reference policy bundles
|   |-- fixtures/             Component capability / qualification / runtime-configuration fixtures
|   `-- tests/                Reference test suite
|-- integrations/
|   |-- agent-memory-runtime/ Runtime adapter integration
|   `-- hermes-agent-memory/  Hermes observe/govern integration
|-- scripts/                  Repository validators (schemas, fixtures, links, doctrine boundaries, closeouts)
|-- wiki-src/                 Source for the published wiki
|-- sources/, reports/        External source registry and generated reports
|-- .github/workflows/        58 evidence and validation workflows; validate-doctrine-evidence is the umbrella gate; cli-doctor carries the wheel-install acceptance job
|-- .github/dependabot.yml    Weekly pip (reference/) and grouped github-actions version updates
|-- .gitattributes            LF normalization for text; binary rules for images and fonts
|-- setup.py                  build_py hook only: copies schemas/*.json into reference/agentmem_ref/_schemas/ at build time (fails on zero copies); metadata stays in pyproject.toml
|-- MANIFEST.in               Carries schemas/*.json into the sdist
`-- .qor/roadmaps/            Committed roadmap topology (agent-memory-1_0-completion)
```

## Interface Contracts

### PAMA (mutation authority)
- **Input**: proposed mutation with target class M0-M5, lifecycle strength, actor scope, evidence pointers
- **Output**: authority decision with downstream authority class A0-A5, handling lane, receipt
- **Side Effects**: durable state change only on grant; audit event emitted; stale-decision protection enforced

### Capability Contract v3 (provider substitution)
- **Input**: provider probe manifest, capability declaration, qualification fixtures
- **Output**: qualification verdict; deterministic routing entry in the component/capability registry
- **Side Effects**: registry mutation; evidence workflow artifacts

### Reference runtime CLI (`agent-memory`)
- **Input**: runtime configuration (validated against `schemas/runtime-configuration.schema.json`), subcommand
- **Output**: validation, discovery, and diagnostic results; exit codes
- **Side Effects**: local substrate files for probes (gitignored `*.kuzu/`); no remote mutation

## Data Flow

```
Observation / inference (probabilistic)
  -> Encoding decision (what deserves to be retained)
  -> Lifecycle state machine (ephemeral -> durable -> consolidated -> forgotten)
  -> PAMA evaluation (uncertainty proposes; authority constrains)
  -> Durable consequence + audit event + receipt
  -> Governed recall planner -> downstream consumers (Qortara, AgentTrust, QOR Agent) via projection profiles
```

## Dependencies

| Package | Justification | Vanilla Alternative |
|---------|---------------|---------------------|
| jsonschema >=4.20,<5 | Schema validation for 58 contracts | no (hand-rolled validation would duplicate the spec) |
| cryptography >=50,<51 | Ed25519 signing and verification for portable evidence, temporal commitments, grants, and external-evidence modules (17 modules) | no |
| rfc8785 >=0.1,<0.2 | RFC 8785 canonical JSON for content digests | no |
| extras `comparators`: agent-manifest 0.11.0, agentrust-trace 0.8.0 | Comparator runners and their tests only; not required by the runtime | n/a |
| setuptools / wheel | Build backend | n/a |
| Python >=3.11 | Runtime floor | n/a |

## Forward Scope (Agent Memory 1.0)

Planning scopes as recorded in the roadmap ledger. Each becomes one or more `/qor-plan` cycles; none is implemented from this genesis.

| Scope | Nodes | Status at genesis |
|---|---|---|
| runtime_core_v1 | runtime_api_boundary, qortara_evolution_delta, pama_runtime_profile, production_state_profile | unresolved (research pending) |
| cognitive_modules_v1 | first_party_qualification, cognitive_plane_completion | unresolved (research pending) |
| production_readiness_v1 | proposed_adr_maturity, qor_agent_proof (#332), trust_evidence_profile, operations_release | unresolved |

Resolved facts carried forward: product_truth, restart_baseline (#282), cognitive_framework (ADR-035 Accepted), capability_fabric, adaptive_state_owner (owner decision: Agent Memory/PAMA owns adaptive-state semantics).

## Governance Controls

- Secret scanning: pre-commit hook plus CI gate to be confirmed by `/qor-deep-audit`; none found in `.github/workflows` at genesis.
- Branch protection: main must restrict force pushes and require the doctrine-evidence workflow (GR-2, GR-3).
- Secrets never enter the ledger, backlog, or feature index.

## Section 4 Razor Pre-Check

Pre-existing state, recorded honestly rather than asserted:

- [ ] All functions <= 40 lines - unverified at genesis; to be measured by `/qor-deep-audit`
- [ ] All files <= 250 lines - **not met**; seven reference modules exceed 550 lines (largest: `runtime_config.py` 732, `capabilities.py` 725). Refactor candidates are backlog items, not genesis blockers.
- [ ] No nesting > 3 levels - unverified at genesis

Any new file planned under `/qor-plan` must meet the razor. Existing violations are tracked in `docs/BACKLOG.md`.

---
*Blueprint sealed. Awaiting GATE tribunal.*
