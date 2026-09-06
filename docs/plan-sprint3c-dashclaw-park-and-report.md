# Plan: Sprint 3c — the DashClaw approved correction parks, and says so

**change_class**: hotfix
**doc_tier**: standard
**risk_grade**: L2
**research_artifact**: docs/research-brief-sprint3c-dashclaw-park-and-report-2026-09-06.md (ledger Entry #29)
**iteration**: 2 (attempt-1 VETO V1-V4 and advisories A1-A3 amended; every assertion below was executed before being locked)

**boundaries**:
- limitations: the correction seam keeps its legacy route and parks; this plan makes the park visible and asserted, it does not give DashClaw corrections a discharge route. The stale-authorization demonstration is lost on this runner path and is recorded as lost, not re-manufactured.
- non_goals: a `TransitionRuleCorpus` for DashClaw corrections (R6, DashClaw-side); forwarding `evidence_for` through `commit_bound_mutation` (LD4 says why not); any change to PR #386; any change to the DashClaw workflow's triggers, environment or pinning beyond listing the new test (LD3).
- exclusions: `reference/agentmem_ref/**` (policy, adapter, evaluator, the DashClaw modules and their `evidence_for`); every fixture and schema; every workflow other than `dashclaw-external-verdict.yml`; the Cloudflare example bundle.

## Open Questions

None.

## Locked Decisions

**LD1 — The runner records the park and asserts the record.** The correction block gains `refusal`, `decision_outcome`, `decision_reasons` and `receipt_decision_outcome` from the fourth commit's `adapter_result`; the assertions change from a commit to the park: `committed is False`, `refusal is None`, `decision_outcome == "require_review"`, `"review_requires_qualified_evidence" in decision_reasons`, `receipt_decision_outcome == "require_review"`, `state_version == 1`, `current_value == "release branch release"`, `old_value_event_invalid is False`, the v1 fact still recall-admitted, and (line 339 inverted) the v1 fact **absent** from `recall_refusals`. The three DashClaw-half refusals stay asserted unchanged. Lines that change: 334-339 and 341; all other assertions were run with the correction parked and hold (scope attack short-circuits on `pama_blocked`; unauthorized and cross-target refuse in the committer).
Grep-evidence for `reference/run_dashclaw_external_verdict.py:334`:
`git show origin/main:reference/run_dashclaw_external_verdict.py | grep -nE 'correction..\.\.committed.. is True' -> 334:    assert report["correction"]["committed"] is True`
Grep-evidence for `reference/run_dashclaw_external_verdict.py:278`:
`git show origin/main:reference/run_dashclaw_external_verdict.py | grep -nE '"committed": correction_commit' -> 278:            "committed": correction_commit.committed,`
Grep-evidence for `reference/agentmem_ref/policy.py:442`:
`git show origin/main:reference/agentmem_ref/policy.py | grep -nE '^REVIEW_REQUIRES_QUALIFIED_EVIDENCE' -> 442:REVIEW_REQUIRES_QUALIFIED_EVIDENCE = "review_requires_qualified_evidence"`

**LD2 — The stale-replay block asserts what the replay now returns, and the report names the lost demonstration.** `stale_replay` becomes `{"committed": False, "refusal": None, "decision_outcome": "require_review"}`; the report gains `"stale_authorization_reachable": False` with a one-line `note` that a committed correction was the precondition. `stale_authorization` is asserted at unit level by `test_governed_paths.py`, `test_restart_safe_runtime.py`, `test_procedural_memory.py`, `test_concurrency_evidence.py` and `test_benchmark_security.py`; no DashClaw test or runner reaches it, and the note says so.
Grep-evidence for `reference/run_dashclaw_external_verdict.py:341`:
`git show origin/main:reference/run_dashclaw_external_verdict.py | grep -nE 'stale_replay.. == ' -> 341:    assert report["stale_replay"] == {"committed": False, "refusal": "stale_authorization"}`

**LD3 — The workflow's inline invariants mirror the runner's, line for line, and the workflow runs the test that substantiates it.** The "Verify workload invariants" step of `dashclaw-external-verdict.yml` re-asserts the runner's correction and stale-replay assertions; its lines 107-110 change to the LD1/LD2 shape so the workflow cannot pass what the runner fails or vice versa. The new test file is added to the workflow's `paths` list (lines 5-18) and to its explicit unittest invocation (lines 61-65), so the DashClaw job runs it; no other trigger, environment or pinning change.
Grep-evidence for line 107 of `.github/workflows/dashclaw-external-verdict.yml`:
`git show origin/main:.github/workflows/dashclaw-external-verdict.yml | grep -nE 'correction..\.\.committed.. is True' -> 107:          assert report["correction"]["committed"] is True`

**LD4 — The seam is not changed, and the reason is asserted, not narrated.** Forwarding `evidence_for(mutation)` to `commit_proposal(evidence=...)` would discharge the medium correction as `delegated_policy` on two `artifact_bound` digests (brief section 4). A new test proves both halves: (a) the approved medium correction through `DashClawGovernedCommitter` parks with the LD1 shape, and the adapter's `commit_proposal` is invoked with `evidence=None` (observed through a subclass whose `commit_proposal` records `kwargs.get("evidence")`, which is `None` because the seam passes no such argument; not by reading source); (b) the same mutation's `evidence_for` items, forwarded directly to `commit_proposal(evidence=...)` on an adapter constructed with an empty `VerifierRegistry` and seeded with the initial promotion first (the correction carries `state_snapshot="v1"`; on an unseeded adapter it refuses `stale_authorization`), **do** commit at medium with `decision.discharge_authority == policy.DELEGATED_POLICY` and `state_version == 2` — the laundering path exists on `asserted` binding alone, with nothing registered, and the seam does not take it. Executed before locking: `committed=True`, `outcome=allow_with_ledger`, `discharge_authority='delegated_policy'`, `review_discharge=''`.
Grep-evidence for `reference/agentmem_ref/dashclaw_external_verdict.py:636`:
`git show origin/main:reference/agentmem_ref/dashclaw_external_verdict.py | grep -nE 'approval_refs=\(approval_ref,\),' -> 636:            approval_refs=(approval_ref,),`

**LD5 — The runtime-evidence document states the park.** `docs/programs/runtime-evidence/dashclaw-external-verdict.md` "Correction" (lines 269-294) ends at "Agent Memory independently revalidates -> require_review parks (review_requires_qualified_evidence)"; "Stale replay" (295-304) states the replay parks the same way and that `stale_authorization` is no longer reached on this path; "Approval and commit boundary" (218-237) gains one paragraph: since ADR-037 4b-2 an approval bound to the exact input identity satisfies the DashClaw half of the seam and no longer discharges PAMA's `require_review`; the route that would is an evaluator-held transition rule, not this document's scope.
Grep-evidence for `docs/programs/runtime-evidence/dashclaw-external-verdict.md:300`:
`git show origin/main:docs/programs/runtime-evidence/dashclaw-external-verdict.md | grep -nE '^committed = false' -> 300:committed = false`

## Phase 1: the test that names both halves

### Affected Files

- `reference/tests/test_dashclaw_correction_parks.py` — new. One `TestCase`, two tests (LD4 a and b), one recording adapter subclass (under 15 lines).

### Unit Tests

- `test_approved_medium_correction_parks_and_forwards_no_evidence` — seeds the initial promotion through the committer, then the approved correction; asserts `committed is False`, `refusal is None`, `adapter_result.decision.outcome == policy.REQUIRE_REVIEW`, `policy.REVIEW_REQUIRES_QUALIFIED_EVIDENCE in adapter_result.decision.reasons`, `adapter_result.receipt["decision_outcome"] == "require_review"`, `memory.state_version(target) == 1`, and the recording adapter's last `commit_proposal` call recorded `evidence` as `None`. Red on `origin/main`? No: this test passes on `main` today — it asserts the current parked behaviour, which the runner contradicts. The red-then-green unit of this cycle is the runner (Phase 2), which fails on `main` and passes after.
- `test_forwarding_producer_evidence_would_discharge_at_medium` — on an adapter constructed with an empty `VerifierRegistry`, commits the initial promotion, then builds the correction proposal with `review_satisfied=False, approval_refs=()` and calls `commit_proposal(proposal, fact_text, evidence=dashclaw.evidence_for(mutation))`; asserts `committed is True`, `decision.outcome == policy.ALLOW_WITH_LEDGER`, `decision.discharge_authority == policy.DELEGATED_POLICY`, `state_version == 2`. This is the hazard, asserted so it cannot be introduced by accident; nothing is registered, which is the point.

## Phase 2: the runner and its mirror

### Affected Files

- `reference/run_dashclaw_external_verdict.py` — correction block fields and assertions 334-339 (LD1); stale-replay block, assertion 341 and note (LD2).
- `.github/workflows/dashclaw-external-verdict.yml` — invariant lines 107-110; `paths` entry and unittest list entry for the new test (LD3).

### Unit Tests

- The runner is its own test: `PYTHONPATH=reference python reference/run_dashclaw_external_verdict.py > out.json` exits 1 on `origin/main` (assertion at line 334) and exits 0 after, writing the evidence file; the workflow's invariant block, run locally against `out.json`, exits 0.

## Phase 3: the document

### Affected Files

- `docs/programs/runtime-evidence/dashclaw-external-verdict.md` — three sections per LD5.

### Unit Tests

- `python scripts/validate_markdown_links.py docs/programs/runtime-evidence/dashclaw-external-verdict.md` — links resolve. Prose accuracy is verified by the seal's reality check against the runner's actual output (LD1/LD2 values quoted in the document must equal the report's).

## Definition of Done

### Deliverable: the runner and workflow report the park

- **D1**: the CI evidence for the DashClaw workload records that an exactly-approved medium correction parks under ADR-037 4b-2, with the adapter's reason, instead of asserting a commit that no longer happens.
- **D2**: `run_dashclaw_external_verdict.py` correction block carries `refusal`, `decision_outcome`, `decision_reasons`, `receipt_decision_outcome`; `stale_replay` carries `decision_outcome`; report carries `stale_authorization_reachable: False`; assertions 334-339 and 341 per LD1/LD2; workflow lines 107-110 plus the test's `paths` and unittest entries per LD3.
- **D3**: ledger SESSION SEAL (#32; audit VETO #30, audit PASS #31); `docs/GOVERNANCE_INDEX.md` plan row; Shadow Genome Failure #7 resolution FIXED; `docs/FEATURE_INDEX.md` FX021; `docs/SYSTEM_STATE.md` counts.
- **D4**: runner exit 1 on `origin/main`, exit 0 after, evidence JSON written; the workflow's invariant block executed locally against that JSON exits 0.

### Deliverable: the seam's non-forwarding is asserted

- **D1**: the laundering path (producer digests discharging a medium correction) is named by a test, and the seam is shown not to take it.
- **D2**: `reference/tests/test_dashclaw_correction_parks.py` with the two tests in Phase 1.
- **D3**: FX021 row cites it.
- **D4**: both tests pass; adversarial negative: a one-line change to `commit_bound_mutation` that forwards `evidence_for(mutation)` makes test (a) fail -- first on `committed is False` (medium accepts `asserted` binding, so the forwarded seam commits) -- and makes the runner's correction assertions fail (applied, observed, reverted; recorded in the seal).

### Deliverable: the document

- **D1**: the runtime-evidence document describes what the workload does now.
- **D2**: three sections per LD5.
- **D3**: none beyond the seal.
- **D4.d**: prose; verified by the seal's reality check that quoted values match the runner's report. **Follow-up phase**: none needed.

## Feature Inventory Touches

| entry_id | operation | test_path | test_descriptor |
|---|---|---|---|
| FX021 | NEW | `reference/tests/test_dashclaw_correction_parks.py` | an exactly-approved medium DashClaw correction parks with `require_review` / `review_requires_qualified_evidence` and `commit_proposal` receives no evidence; forwarding the producer's digests commits at medium with `discharge_authority == delegated_policy` |

## CI Commands

- `python -m unittest reference.tests.test_dashclaw_correction_parks` — the two LD4 tests.
- `PYTHONPATH=reference python reference/run_dashclaw_external_verdict.py > out.json` — the CI runner; exit 0 and evidence written.
- `python -m unittest discover -s reference/tests -t reference` — full suite.
- `python scripts/validate_schemas.py` and `python scripts/validate_fixtures.py fixtures` — unchanged surfaces stay clean.
- `python scripts/validate_markdown_links.py docs/programs/runtime-evidence/dashclaw-external-verdict.md` — document links.
- `python scripts/verify_seals.py` — anchors match.
