# Project Backlog

This file is the current repository-level work queue. Historical sprint plans and ledger entries explain prior decisions; open GitHub issues carry the detailed acceptance criteria for unresolved work.

## Blockers (Must Fix Before Production-Readiness Claims)

### Security Blockers
- [ ] [S1] Issue #364: close the remaining recall/scope authority legs. The embedding host remains the declared authenticator for `RecallContext.principal_ref`; shared-domain membership and write-side scope expansion still need governed authority enforcement.

### Development Blockers
- [ ] [D1] Issue #395: reconcile the `approve`/`commit` attestation asymmetry so an attestation accepted by approval is not silently ignored by commit unless that stronger requirement is made explicit doctrine.
- [ ] [D2] Issue #363: define and implement the production state profile. The current checkpoint path is in-memory-specific and private-attribute-coupled; non-toy substrate persistence and durable runtime state remain incomplete.

## Backlog (Planned Work)
- [ ] [B1] `runtime_core_v1` — **partially complete**. Public Python contract `1.2.0` now exposes schema-backed proposal, decision/approval, commit, recall, history, posture, action-authority, and execution-evidence stages. Remaining work is #395, #364, #363, and the deliberately held JS/PAMA parity slice from Sprint 4b.
- [ ] [B2] `cognitive_modules_v1` — resolve remaining first-party qualification and cognitive-plane completion work against current implementation evidence before opening new conceptual surface area.
- [ ] [B3] `production_readiness_v1` — complete external/runtime proof rather than inferring production readiness from repository tests: QOR proving ground #332, live DashClaw conformance #361, governed knowledge profile #387, and longitudinal efficacy program #388. PR #389 supports the efficacy program but must be reconciled against current `main` before merge.
- [ ] [B4] Section 4 Razor — assess/refactor legacy reference modules above the repository's size/complexity thresholds without weakening governance or evidence controls.
- [x] [B5] Repository security baseline — secret scanning, push protection, CodeQL, private vulnerability reporting, and Dependabot configuration confirmed/landed during Sprint 1.
- [ ] [B6] Issue #392: DashClaw correction discharge route. Keep parked until rule authorship/ownership for an evaluator-held `TransitionRuleCorpus` is decided; do not substitute authority or repeated agreement for evidence that the transition is correct.

## Explicit Holds
- **Sprint 4b / JS PAMA parity**: held after audit veto. The draft port matched Python policy evaluation but would have made every correction non-committable because no discharge path was ported in the same cycle. Resume only with a complete correction/remediation route.
- **DashClaw #392**: blocked on a DashClaw-side rule-authorship decision.

## Completed Since the Previous Backlog Snapshot
- Public API contracts `1.0.0`, `1.1.0`, and `1.2.0` landed through PRs #394, #397, and #398.
- ADR-037 fail-closed review/remediation path is implemented in the Python reference runtime.
- ADR-038 added `action_execution` and bound action authority/execution evidence to PAMA decisions.
- Latest recorded reference suite at `main` `56e44d3`: 1195 tests, 0 failures, 7 skipped under the declared pinned environment; this is repository evidence, not a production-readiness claim.

---
_Last reconciled against `main` `56e44d3cd3cb9c4186596f6a064dd554d14c1940` on 2026-09-12._
