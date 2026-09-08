# Public API Contract

**Status**: contract version `1.2.0`. `1.0.0` (Sprint 4a, plan `docs/plan-sprint4a-public-api-contract.md`, ledger Entry #45) implemented PRD-001 R1's proposal, decision, approval, commit, retrieval-candidate and recall-admission stages; `1.1.0` (Sprint 4c-1, plan `docs/plan-sprint4c1-history-posture.md`, Entry #51) added the history/provenance and posture inspection operations; `1.2.0` (Sprint 4c-2, plan `docs/plan-sprint4c2-action-authority.md`, ADR-038) adds the action-authority and execution-evidence stages. The JS runtime's conformance is Sprint 4b, held (Entry #47).

## What the contract is

An embedding host calls nine functions in `agentmem_ref.api.surface` -- five memory stages that take a `GovernedMemoryAdapter` and an envelope, two read-only inspections, and two action stages -- each returning a **result envelope**. The envelopes are schema-backed and carry a **contract version**; the adapter's internal dataclasses (`Proposal`, `RecallContext`, `CommitResult`, `AdmissionResult`) stay behind the surface and are not the contract.

| Envelope | Schema | Term |
|---|---|---|
| proposal envelope | `schemas/api-proposal-envelope.schema.json` | the public form of a proposal: exactly the 24 `Proposal` fields a consumer may set |
| recall context envelope | `schemas/api-recall-context.schema.json` | the public form of a recall context |
| result envelope | `schemas/api-result-envelope.schema.json` | what every stage returns: contract version, compatibility, stage, decision projection, and stage-specific fields |
| target envelope | `schemas/api-target-envelope.schema.json` | names one governed memory target for a read-only inspection (`history`) |
| posture report | `schemas/api-posture-report.schema.json` | the doctor's report as `posture` returns it |
| action envelope | `schemas/api-action-envelope.schema.json` | the public form of an action proposal: the proposal envelope's fields with `operation` fixed to `action_execution`, `state_snapshot` required, and the action named (`action_id`, `description`, `skill_version_ref`) |
| execution observation | `schemas/api-execution-observation.schema.json` | what a host observed about an execution (`witness_ref`, `enforcement_mode`, `delivery_status`, `enforcement_point_status`, `action_status`, `liveness_status`, `observed_at`, optional `evidence_refs`); `observed_at` is host-asserted text |

Examples a consumer can start from: `reference/fixtures/api/proposal-envelope.example.json`, `reference/fixtures/api/recall-context.example.json`, `reference/fixtures/api/target-envelope.example.json`, `reference/fixtures/api/action-envelope.example.json`, `reference/fixtures/api/execution-observation.example.json`.

## Contract version and compatibility

Every envelope carries `contract_version`. Before any stage runs, the surface evaluates it against the implementation's `CONTRACT_VERSION` using ADR-030's four compatibility states, and the result envelope records the state:

| state | when | what runs |
|---|---|---|
| `current` | same major, envelope minor not higher than the implementation's (an older minor is understood in full) | the stage |
| `migration_required` | same major, envelope minor higher than the implementation's (it may carry fields this implementation lacks) | nothing; `stage: none` |
| `incompatible` | different major | nothing; `stage: none` |
| `unknown` | field absent or unparseable | nothing; `stage: none` |

Contract `1.0.0` shipped this rule inverted (an older minor was reported `migration_required`); `1.1.0` corrected it, and the correction is the plan's reasoning about additive minors -- ADR-030 supplies the four states and the rule that `unknown` is not current, not the direction.

Schema validation is a second, separate check ("serialization success is not semantic compatibility", ADR-030): a `current` envelope that fails its schema returns `stage: none` with `validation_error` naming the property.

## The stages

| function | stage | writes? | what it does |
|---|---|---|---|
| `propose(memory, envelope)` | `proposal` (and `decision`, as the projection every result carries) | no | validates, converts, runs the base PAMA evaluation, returns the decision projection |
| `approve(memory, envelope, *, evidence=(), attestation=None)` | `approval` | no | the ADR-037 4a discharge: qualified evidence grouped and verified through the **adapter's own** registry, or an attestation for `require_external_verification`; returns the decision with `discharge_authority` / `review_discharge` |
| `commit(memory, envelope, fact_text, *, evidence=(), attestation=None)` | `commit` | yes, or parks | forwards evidence and attestation unchanged to `commit_proposal`; returns the receipt, `committed`, `fact_uuid`, `refusal` |
| `recall(memory, query, context_envelope)` | `recall` (retrieval candidate and recall admission) | no | `candidates` are the retrieval candidates; `admissions` are the adapter's per-candidate decision records (`outcome`: `admit` / `block`, `reason_code`), passed through unchanged; `admitted` is the admitted subset |
| `forget(memory, envelope, *, evidence=(), attestation=None)` | `forget` | yes, or parks or refuses | resolves the target's current fact and forwards to `governed_delete`; an unknown target refuses `fact_not_found` |
| `history(memory, target_envelope, *, fact_text=None)` | `history` (inspect history/provenance) | no | the target's retained audit events (commit and deletion events; recall events carry no target and are read from `memory.events` directly), `current_fact_uuid`, `state_version`, `tombstoned`, and, given a value, that value's rejected-value history (recorded when a committed correction superseded it) |
| `posture(config_path, *, qualification_path=None, state_dir=None)` | `posture` (inspect configured posture) | no | the doctor's report for a configuration, validated against `api-posture-report`; takes paths, not an adapter, and emits `compatibility: current`; a missing or invalid configuration returns `stage: none` with `validation_error` |
| `authorize(memory, action_envelope, *, evidence=(), attestation=None)` | `action_authority` | binds, or not | the adapter evaluates the action as a PAMA `action_execution` proposal through its own registry; a terminal outcome binds an executable allow or a deny **after** the PAMA decision document, the receipt and the receipt event exist; a review outcome, or any outcome reached by discharging an authority-class floor, binds nothing; returns the decision projection (with `constraints`) and an `action_authority` object; a refused call (reused ids, ledger failure) returns `refusal` and no `action_authority` key |
| `witness(memory, observation_envelope)` | `execution_evidence` | consumes | binds the host's observation to the decision the adapter bound and returns the execution witness; consumes the execution authorization exactly once at the seam; refuses (`refusal`, no `witness` key) when no decision is bound or the authorization is already consumed |

The decision projection carries `outcome`, `permitted_actions`, `prohibited_actions`, `reasons`, `policy_version`, `discharge_authority`, `review_discharge` and, since `1.2.0`, `constraints`: the active governance constraints the decision carries (`risk_cell` always; `authority_floor:<class>` for A4/A5; `target_floor:<class>` for M4/M5), derived from the proposal so no discharge removes them (ADR-038). The base evaluation records no reason string when nothing was claimed: a medium-risk correction proposed without evidence returns `require_review` with `enter_pending_verification` among its permitted actions and an empty `discharge_authority`.

## What the surface refuses, and why

- **An asserted review.** The proposal envelope rejects `review_satisfied`, `approval_refs`, `approves_own_authority` and `actor_authority_resolved` (`additionalProperties: false`). Those are evaluator-side fields; a caller-asserted approval is the route ADR-037 step 4b-2 removed, and the contract cannot express it.
- **A caller-supplied verifier.** No function accepts a verifier or a registry. Verifier trust is the adapter's (`VerifierRegistry` passed at construction), never the proposer's.
- **A stage on a non-current version.** See the compatibility table.
- **An action through the memory stages.** `propose`, `approve` and `commit` refuse `operation: action_execution` at validation; an action has its own stages. The action envelope in turn refuses `requires_governance`, `outcome`, `decision_ref` and every other assertion field, and the observation envelope refuses `effective_decision`, `decision_alignment` and every approval field: the adapter decides, the builder aligns, the host executes and observes.

## What `commit` forwards and what the adapter does with it

`commit` and `forget` forward both `evidence` and `attestation` unchanged (DoD 20, asserted by `reference/tests/test_api_dod20.py` through a recording adapter). The adapter's two seams differ in what they do with an attestation alone:

- `governed_delete` selects three ways: evidence (with optional attestation) -> qualified-evidence discharge; attestation alone -> external-verification discharge; else the base evaluation.
- `commit_proposal` selects two ways: evidence -> qualified-evidence discharge (the attestation is passed along); else the base evaluation. **An attestation without evidence is ignored there.** `approve` uses the three-way selection (`GovernedMemoryAdapter.evaluate_proposal`), so a consumer can see a critical correction discharge at `approve` and then park at `commit` unless evidence accompanies the attestation. This asymmetry is pre-existing, pinned by `test_commit_attestation_only_is_ignored_by_the_adapter_today`, and raised as a follow-up rather than changed here: aligning `commit_proposal` is a behaviour change to a seam 48 files call.

## Action authority and execution evidence (contract `1.2.0`, ADR-038)

An action is authorized by an ordinary PAMA decision on a proposal whose operation is `action_execution` (`docs/33` gives it four cells: low `allow_with_ledger`, medium and high `require_review`, critical `require_external_verification`). `memory/action_authority.py` hosts the path with the runtime adapter as an injected collaborator; the adapter learns nothing about actions.

- **Terminal outcomes bind; review outcomes do not.** `allow`/`allow_with_ledger` bind an executable allow at `procedural_memory.apply_action_governance`; `block` binds deny; `require_review`/`require_external_verification` bind nothing, and the `requirement` field names the governance step as vocabulary (`enter_pending_verification` / `request_external_verification`). An unbound action is **not** the memory path's parked state: no `memory.pending_verification` record is written and the same proposal is not resumable here; the route for an A0-A3 action is re-proposal with evidence under fresh `proposal_id` and `action_id`. A host may not execute merely because no denial object exists.
- **Authority-class floors are not dischargeable on this path.** A decision that reached `allow` only by discharging an A4 or A5 floor (visible in `constraints`) binds nothing; A4 actions park with `enter_pending_verification` and A5 with `request_external_verification`. In `1.2.0` an executable allow therefore binds only for A0-A3 actions; A4/A5 actions await a governance mechanism outside this path. Deny still binds for every class. Target-class floors keep the memory path's discharge behaviour.
- **A bound decision has its ledger first.** Before a bound decision is exposed the path builds the PAMA decision document (`pama-decision:<proposal_id>`), the receipt naming it and an `action.receipt` event; if any step fails, nothing binds. `ledger_required` reports `allow_with_ledger`.
- **A witness requires a bound decision, allow or deny.** The host supplies observations; `build_execution_witness` computes `decision_alignment` from the bound composition. A deny-bound execution is recorded as `violation`; an unbound execution report becomes an `action.unbound_execution_reported` audit event and is refused. One bound decision may carry several witnesses (`prevented`, `refused`, ...) and exactly one consumption.
- **Single consumption.** An `executed` observation against a bound allow consumes the authorization at `record_runtime_execution`; a second one is refused at the seam (`execution authorization already consumed`) and never witnessed `consistent`. Consumption is keyed on the decision identity (`proposal_id`) and the action identity (`action_id`): neither may be reused on this path.
- **Consumption survives restart, for state a checkpoint captured.** The consumption records live in the adapter's `extension_state`, which `restart_runtime` snapshots beside `events` and restores fail-closed (a malformed slot refuses every later call). `RestartSafeRuntime` checkpoints after memory commits and deletes and cannot wrap this module, so a host on it must call `checkpoint()` after `witness`; the window between consumption and that checkpoint is the host's. `extension_state` is adapter-owned ledger state on the same footing as `adapter.events`, not a host interface, and the module exposes no setter.
- **Known namespace limitation.** Memory commits do not record proposal ids into the action-consumption namespace, so the same identifier may presently appear once in the memory path and once in the action path; uniqueness is enforced within the governed action path, not globally across PAMA operations. Global proposal/action identity coordination is future work.
- **Caller-declared classification.** `downstream_authority` and `risk_class` are declared on the envelope; nothing yet cross-checks them against the skill. `state_snapshot` is an identity input to the enforcement projection, not a staleness gate. Action events carry `memory_id = action_id`, so `history(action_id)` lists them and `history(target)` does not.

## Sprint 4b (held)

The JS runtime's conformance under this contract is Sprint 4b, held at Entry #47.
