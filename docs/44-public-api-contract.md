# Public API Contract

**Status**: contract version `1.1.0`. `1.0.0` (Sprint 4a, plan `docs/plan-sprint4a-public-api-contract.md`, ledger Entry #45) implemented PRD-001 R1's proposal, decision, approval, commit, retrieval-candidate and recall-admission stages; `1.1.0` (Sprint 4c-1, plan `docs/plan-sprint4c1-history-posture.md`, Entry #51) adds the history/provenance and posture inspection operations. Action authority and execution evidence are Sprint 4c-2, held for ideation because their decision is caller-supplied today (research brief `docs/research-brief-sprint4c-remaining-stages-2026-09-07.md`, section 2); the JS runtime's conformance is Sprint 4b, held (Entry #47).

## What the contract is

An embedding host calls seven functions in `agentmem_ref.api.surface` -- five stages that take a `GovernedMemoryAdapter` and an envelope, and two read-only inspections -- each returning a **result envelope**. The envelopes are schema-backed and carry a **contract version**; the adapter's internal dataclasses (`Proposal`, `RecallContext`, `CommitResult`, `AdmissionResult`) stay behind the surface and are not the contract.

| Envelope | Schema | Term |
|---|---|---|
| proposal envelope | `schemas/api-proposal-envelope.schema.json` | the public form of a proposal: exactly the 24 `Proposal` fields a consumer may set |
| recall context envelope | `schemas/api-recall-context.schema.json` | the public form of a recall context |
| result envelope | `schemas/api-result-envelope.schema.json` | what every stage returns: contract version, compatibility, stage, decision projection, and stage-specific fields |
| target envelope | `schemas/api-target-envelope.schema.json` | names one governed memory target for a read-only inspection (`history`) |
| posture report | `schemas/api-posture-report.schema.json` | the doctor's report as `posture` returns it |

Examples a consumer can start from: `reference/fixtures/api/proposal-envelope.example.json`, `reference/fixtures/api/recall-context.example.json`, `reference/fixtures/api/target-envelope.example.json`.

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

The decision projection carries `outcome`, `permitted_actions`, `prohibited_actions`, `reasons`, `policy_version`, `discharge_authority`, `review_discharge`. The base evaluation records no reason string when nothing was claimed: a medium-risk correction proposed without evidence returns `require_review` with `enter_pending_verification` among its permitted actions and an empty `discharge_authority`.

## What the surface refuses, and why

- **An asserted review.** The proposal envelope rejects `review_satisfied`, `approval_refs`, `approves_own_authority` and `actor_authority_resolved` (`additionalProperties: false`). Those are evaluator-side fields; a caller-asserted approval is the route ADR-037 step 4b-2 removed, and the contract cannot express it.
- **A caller-supplied verifier.** No function accepts a verifier or a registry. Verifier trust is the adapter's (`VerifierRegistry` passed at construction), never the proposer's.
- **A stage on a non-current version.** See the compatibility table.

## What `commit` forwards and what the adapter does with it

`commit` and `forget` forward both `evidence` and `attestation` unchanged (DoD 20, asserted by `reference/tests/test_api_dod20.py` through a recording adapter). The adapter's two seams differ in what they do with an attestation alone:

- `governed_delete` selects three ways: evidence (with optional attestation) -> qualified-evidence discharge; attestation alone -> external-verification discharge; else the base evaluation.
- `commit_proposal` selects two ways: evidence -> qualified-evidence discharge (the attestation is passed along); else the base evaluation. **An attestation without evidence is ignored there.** `approve` uses the three-way selection (`GovernedMemoryAdapter.evaluate_proposal`), so a consumer can see a critical correction discharge at `approve` and then park at `commit` unless evidence accompanies the attestation. This asymmetry is pre-existing, pinned by `test_commit_attestation_only_is_ignored_by_the_adapter_today`, and raised as a follow-up rather than changed here: aligning `commit_proposal` is a behaviour change to a seam 48 files call.

## Deferred to Sprint 4c-2

Action authority (`procedural_memory.apply_action_governance`) and execution evidence (`record_runtime_execution`) have no envelope form. The only implementation of action authority binds a **caller-supplied** decision, which at the boundary is the assertion shape ADR-037 4b-2 removed; the honest sources of an action decision (a PAMA operation for actions, or an external governance projection) are a concept decision, so 4c-2 begins with ideation. The JS runtime (Sprint 4b) is held at Entry #47.
