# Plan: Sprint 2f — verified discharge of external verification

**change_class**: feature
**Risk Grade**: L3
**Session**: 2026-09-04T1754-81306b
**Research**: `docs/research-brief-sprint2f-verified-discharge-2026-09-04.md`
**Iteration**: 2 (amended for audit attempt 1 grounds V1-V3)
**Gap**: GAP-ARCH-04 — external-verification leg

## Objective

Stop `policy.evaluate` discharging `require_external_verification` on a caller-asserted boolean, and give a caller with genuinely verified authority an explicit, proposal-bound channel to use instead.

## Boundaries

**In scope**: `reference/agentmem_ref/policy.py`, `reference/agentmem_ref/decision_overwrite.py`, `reference/agentmem_ref/structural_mutation.py` (audit V1), six amended tests (§Disclosure), new tests.

**Non-goals**: the 74 `require_review` discharges — capping external verification does not touch them, and they remain open under GAP-ARCH-04.

## What this does and does not achieve — stated first

**Achieves**: ordinary `policy.evaluate` can no longer discharge `require_external_verification` at all. The `"i-said-so"` channel is capped at `require_review`. A caller wanting external verification must use an explicit entry point and supply an attestation that policy checks *relationally against the proposal*.

**Does not achieve**: an unforgeable attestation. `ExternalVerification` is still constructed by the caller, so an actor who can build a `Proposal` can build one. What changes is that it is no longer a **boolean** — it carries facts policy cross-checks (binding to this proposal, verifier distinct from actor, authority kind, risk ceiling) — and the assertion path is closed off entirely.

Making the attestation unforgeable means applying Loop 6's registry pattern to attestations: written at verification time by the verifier, resolved rather than trusted. That is a further cycle and is **not** claimed here. This plan states the limit because the Loop 6 audit caught precisely this class of overclaim, where a control was described as stronger than its trust boundary allowed.

## Design decisions

**LD1 — `_apply_review` caps at `require_review`.**
When the outcome is `REQUIRE_EXTERNAL_VERIFICATION`, an asserted discharge no longer collapses it to `allow_with_ledger`. The outcome is returned unchanged with the reason `external_verification_requires_attestation`.

`require_review` discharge is untouched: 74 sites keep working, and this cycle takes no position on them.

**LD2 — `ExternalVerification`, a frozen attestation, not a flag (research F4).**
A dataclass carrying `bound_proposal_id`, `verifier_principal_id`, `authority_kind`, `max_risk_class`. Deliberately **not** a `verified: bool` on `Proposal`, which would be a fourth caller-asserted boolean and would let `"i-said-so"` become `"i-said-so", verified=True`.

**LD3 — `evaluate_with_external_verification`, mirroring the existing bridge.**
A new entry point that checks the attestation relationally against the proposal before permitting the discharge:

| Check | Refusal |
|---|---|
| `bound_proposal_id == proposal.proposal_id` | `attestation_not_bound_to_proposal` |
| `verifier_principal_id != proposal.actor_id` | `attestation_self_verified` |
| `authority_kind == "human_confirmation"` when risk is high or critical | `human_confirmation_required` |
| `risk_class <= max_risk_class` | `attestation_risk_ceiling_exceeded` |

The binding check is what stops an attestation being reused across proposals; the verifier check derives self-verification from identity, as Loop 5 did for self-approval. Shape mirrors `evaluate_pama_with_reusable_grant`, which is already the repository's pattern for "evidence-gated discharge through a dedicated entry point".

**LD4 — `Decision.review_discharge` gains `verified`.**
Loop 5 reserved the value and produced only `asserted`. This cycle produces it, on the attested path only. The field now distinguishes the three states an evaluation can be in: `""` (no discharge), `asserted`, `verified`.

**LD6 — `structural_mutation.evaluate_pama_v13` is brought into scope with coverage (audit V1).**

`structural_mutation.py:430-439` passes `base_outcome=REQUIRE_EXTERNAL_VERIFICATION` with `allow_review_discharge=True`, so LD1's cap changes its behaviour. **No test reaches that discharge** — instrumentation across all 937 tests records zero external-verification discharges originating there — so a green suite would have proved nothing about it.

`evaluate_pama_v13` gains an optional `external_verification` parameter, forwarded to the same attested path. A structural mutation at high or critical risk now requires an attestation exactly as any other external-verification outcome does, which is the consistent result rather than a special case.

Coverage is added rather than assumed: a new test drives `evaluate_pama_v13` at critical risk both without an attestation (capped at `require_external_verification`) and with one (discharged). Without this the cycle would change an uncovered production path silently — the failure shape DoD 8 cannot see.

**LD5 — `decision_overwrite` routes through the new entry point.**
Research F1 established its grant validation already exceeds what the attestation requires: it binds the grant to the proposal and target, derives self-approval from identity, enforces a risk ceiling, and requires `HUMAN_CONFIRMATION` for high or critical risk. It builds an `ExternalVerification` from the grant it has already validated and calls the new entry point, replacing `review_satisfied=True`.

This is not new authority. It is the same authority, expressed in a channel that can be told apart from assertion.

## Disclosure — the first amended pre-existing test

Five seals have cited "no prior test amended" as evidence. This cycle breaks that, and does so deliberately.

**Six tests, not two (audit V2).** The plan's first draft reused Loop 5's four-site measurement instead of re-running it. Current instrumentation over all 937 tests:

| Site | Operation |
|---|---|
| `test_decision_overwrite.py:145` | `decision_overwrite` |
| `test_decision_overwrite_fixtures.py:121` | `decision_overwrite` |
| `test_deletion_authority.py:79` | `permanent_deletion` |
| `test_deletion_authority.py:106` | `permanent_deletion` |
| `test_derived_authority.py:63, 81, 97, 120` | `policy_mutation` |

The two `decision_overwrite` sites are carried by LD5's routing and need no edit. The rest are amended to supply an `ExternalVerification` — which is what a caller performing a critical permanent deletion or policy mutation should have had all along.

**One amendment has a governance consequence and is named.** `test_derived_authority.py:81` is `test_third_party_discharge_still_works`, which asserts that `policy_mutation/critical` with a third-party approval yields `allow_with_ledger`. **That test is Loop 5's DoD 3, cited as evidence in ledger Entry #15.**

Amending it is legitimate: Entry #15 recorded what was true then, and this cycle deliberately narrows that behaviour through the governed chain, which is the mechanism for exactly this. But a test that a prior seal rests on is not amended quietly. The seal for this cycle names Entry #15 and states what changed, so a reader of the ledger can follow the narrowing rather than discover a contradiction between two entries.

**Research F5 is stale for the same reason (audit V3)** and the measurement above supersedes it.

## Affected files

| File | Change |
|---|---|
| `reference/agentmem_ref/policy.py` | LD1 cap; `ExternalVerification` (LD2); `evaluate_with_external_verification` (LD3); `verified` discharge value (LD4) |
| `reference/agentmem_ref/decision_overwrite.py` | route through the new entry point (LD5) |
| `reference/agentmem_ref/structural_mutation.py` | optional `external_verification` on `evaluate_pama_v13` (LD6) |
| `reference/tests/test_deletion_authority.py` | **amended** — two fixtures |
| `reference/tests/test_derived_authority.py` | **amended** — four sites, one of them Entry #15 evidence |
| `reference/tests/test_verified_discharge.py` | **new** |

## Feature Inventory Touches

| ID | Feature | Disposition |
|---|---|---|
| FX011 | External verification is dischargeable only through a proposal-bound attestation, never by assertion | NEW |
| FX009 | Review discharge provenance | MODIFIED — now produces `verified` |

## Definition of Done

1. `policy.evaluate` with `review_satisfied=True, approval_refs=("i-said-so",)` on `policy_mutation/critical` returns `require_external_verification`, **not** `allow_with_ledger`. It previously returned the latter.
2. The same for `scope_expansion/high` and `permanent_deletion/critical`.
3. `require_review` discharge is unchanged — a third-party assertion still yields `allow_with_ledger` with `review_discharge == "asserted"`.
4. A bound, non-self, human-confirmation attestation discharges `require_external_verification`, with `review_discharge == "verified"`.
5. Each attestation check refuses by name: unbound, self-verified, wrong authority kind at critical risk, risk ceiling exceeded.
6. An attestation bound to a *different* proposal id is refused — it cannot be replayed.
7. `decision_overwrite` still commits its high-risk overwrite end to end, now via the attested path, and `_grant_refusal`'s existing refusals are unchanged.
8. **All prior tests pass except the six declared amendments**, whose diff is limited to supplying an attestation.
8b. `evaluate_pama_v13` at critical risk is **covered in both directions**: capped at `require_external_verification` without an attestation, discharged with one. This path had zero coverage before this cycle (audit V1).
9. `validate_schemas.py` and `validate_fixtures.py fixtures` clean; no schema modified.
10. The seal records that the attestation is caller-constructed and therefore forgeable, and that making it unforgeable is a further cycle.

## CI Commands

```
python -m unittest discover -s reference/tests -t reference
python scripts/validate_schemas.py
python scripts/validate_fixtures.py fixtures
```

## CI Coverage Exemptions

All policy-path evidence workflows are triggered. DoD 8 covers them.

## Rollback

`git checkout -- reference/agentmem_ref/policy.py reference/agentmem_ref/decision_overwrite.py reference/tests/test_deletion_authority.py` and delete the new test file. The tree is now committed at `fe7724e`, so rollback is a clean revert rather than a discard.

## Next

`/qor-audit`. L3: adversarial mode; independent verification that the cap cannot be circumvented through `evaluate_with_base_outcome`, and that LD5 grants `decision_overwrite` no authority it did not already have.
