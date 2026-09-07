# Research Brief: Sprint 4c — the remaining PRD-001 R1 stages, measured before they get boundary forms

**Date**: 2026-09-07
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 22.
**Implements**: the operator's 2026-09-07 direction ("go on with 4c") after Sprint 4b was held (Entry #47); issue #362's remaining stages after Sprint 4a (Entry #45) froze contract `1.0.0` for six of eight
**Scope**: PRD-001 R1's action-authority and execution-evidence stages, and its history/provenance and posture-inspection operations: what exists, what already has a record form, and where a public entry point would have to invent a decision it must not invent

## 1. What 4a left open

Contract `1.0.0` (`docs/44-public-api-contract.md`) covers proposal, decision, approval, commit, retrieval candidate and recall admission. PRD-001 R1 (`docs/prd/PRD-001-configurable-agent-memory-runtime.md:115-130`) also names **action authority** and **execution evidence** as stages, and **inspect history/provenance**, **inspect decision/receipt evidence**, **inspect configured component/capability posture** and **inspect adapter/qualification posture** as operations. This brief measures each.

## 2. Action authority: the decision is caller-supplied today

`reference/agentmem_ref/memory/procedural_memory.py:574-593`, `apply_action_governance(action, decision)`: an `ActionProposal` (`:196-203`: `action_id`, `description`, `skill_version_ref`, `requires_governance`, `governance_decision_ref`, `execution_status`, `execution_ref`) is bound to an `ActionGovernanceDecision` (`:207-210`: `decision_ref`, `action_id`, `outcome`) that **the caller supplies**. The docstring says so: "A skill cannot manufacture this decision; the caller must supply it from the Runtime/Governance path." The function checks only that the decision names the action; `outcome == "deny"` blocks, anything else authorizes (`execution_status = "authorized_not_executed"`).

At the public boundary that is the shape ADR-037 4b-2 removed from proposals: an outcome asserted by the party presenting it. Nothing in the repository produces an `ActionGovernanceDecision` from an evaluation -- the base table has no action operation, and the runtime does not route actions through PAMA. The five call sites are all in `reference/tests/test_procedural_memory.py`, which constructs the decision by hand. So a public `authorize_action(envelope, decision_envelope)` would let a consumer authorize its own action by supplying `outcome: "allow"`, unless the decision comes from somewhere the consumer does not control. Two honest sources exist in the repository's doctrine and neither is wired: a PAMA evaluation of the action as a proposal (an `operation` for actions would have to be added to the table -- doctrine, `docs/33-pama-decision-table.md`, not this program's to extend), or an external governance projection record (`schemas/external-policy-decision.schema.json`, `external-enforcement-decision-projection.schema.json`, the DashClaw / Agent Governance seam). **This is a concept decision, not a plan item.**

## 3. Execution evidence: a boundary form already exists

`record_runtime_execution(action, execution_ref)` (`:595-601`) refuses unless the action is `authorized_not_executed` with a bound `governance_decision_ref`, then records `execution_ref` and `executed_by_runtime`. The record form for execution evidence exists: `schemas/execution-witness.schema.json` (required: `witness_id`, `input_identity`, `composition_id`, `action_ref`, `witness_ref`, `effective_decision` ∈ allow/warn/require_approval/deny, `enforcement_mode`, `delivery_status`, `enforcement_point_status`, `action_status` ∈ executed/prevented/refused/unknown/not_observed, `decision_alignment` ∈ consistent/stricter_than_decision/violation/unverifiable, `liveness_status`, `approval_evidence_status`, `observed_at`, `evidence_refs`, `non_claims`). An `execution_ref` string is far less than a witness; the stage's boundary form is the witness, and it depends on section 2's decision for `effective_decision` and `decision_alignment`. **Sequenced behind section 2.**

## 4. History and provenance: records exist, an entry point does not

- `GovernedMemoryAdapter.rejected_value_history(memory_id, fact_text) -> tuple[dict, ...]` (`runtime/adapter.py:673`) and `tombstoned_ids() -> set[str]` (`:676`): ad hoc shapes.
- Every commit already emits schema-backed `memory-audit-event` records (`CommitResult.events`; `schemas/memory-audit-event.schema.json`, required `event_id`, `event_type`, `event_version`, `timestamp`, `component`), and every governed recall emits one (Entry #13).
- `InMemoryTemporalGraph.write_log: list[tuple[str, str]]` (`state/substrate.py:98`) is an operation log the restart runtime scrapes (#363).

A public `history(memory, target_envelope)` can return, in a result envelope, the audit events for a target, the rejected-value history, and whether the target's current fact is tombstoned -- **all from records that exist**, with the audit events already schema-backed. Provenance beyond that (derivation chains) has its own record, `derivation-evidence.schema.json`, produced by `derivation_evidence` for specific flows; not a general history. **Plan-ready.**

## 5. Posture inspection: reports exist, unschema'd

- `runtime/doctor.py:206` `diagnose(config_path, *, qualification_path=None, ...) -> dict`: the report the CLI prints; no schema.
- `runtime/runtime_config.py:697` `load_runtime_configuration(path, qualification_bindings) -> RuntimeConfigurationPlan`, validated against `runtime-configuration.schema.json` on load.
- `contracts/qualification.py:375` `qualification_from_adapter_results(...)` produces `component-capability-qualification` records (schema exists).

A public `posture(config_path, qualification_path)` can return the doctor report and the loaded configuration plan's summary; the report needs a schema (`api-posture-report`) or the entry point returns the two already-schema-backed inputs (configuration, qualification records) and the doctor's findings as a list. **Plan-ready**, with the schema decision made in the plan.

## 6. Blueprint alignment

| Claim | Source | Finding | Status |
|---|---|---|---|
| Action authority is a stage the API can distinguish | PRD-001 R1 | the only implementation takes a caller-supplied outcome; no evaluator produces it | **DRIFT** -- a public form now would be an assertion route |
| Execution evidence is a stage the API can distinguish | PRD-001 R1 | `execution-witness` is its record; depends on an honest action decision | sequenced |
| History/provenance inspection | PRD-001 R1 | records exist (audit events, rejected values, tombstones); no entry point | plan-ready |
| Posture inspection | PRD-001 R1 | `diagnose` report and configuration plan exist; report unschema'd | plan-ready |

## 7. Recommendation

Split 4c. **4c-1 (plan now)**: `history` and `posture` entry points on the `1.0.0` surface, result-envelope shaped, backed by the records that exist (audit events, rejected-value history, tombstones; configuration plan, qualification records, doctor findings), with contract minor version `1.1.0` (additive; ADR-030 `migration_required` semantics already handle a `1.0.0` consumer). **4c-2 (ideation first)**: action authority and execution evidence, because the decision's source is a concept question -- PAMA operation for actions (doctrine change) or external governance projection (a second party) -- and a public entry point built on `apply_action_governance` as it stands would let the presenter authorize itself.

---

_Research complete. Findings are advisory — implementation decisions remain with the Governor._
