# Shadow Genome

## Purpose

The Shadow Genome documents **failure modes** - approaches that were rejected, patterns that failed, and lessons learned. This creates institutional memory to prevent repeated mistakes.

---

## Failure Categories

| Code | Category | Description |
|------|----------|-------------|
| `COMPLEXITY_VIOLATION` | Section 4 Razor breach | Function/file too long, nesting too deep |
| `SECURITY_STUB` | Incomplete security | TODO/placeholder in auth/security code |
| `GHOST_PATH` | Disconnected UI | UI element without backend handler |
| `HALLUCINATION` | Invalid dependency | Library that doesn't exist or wasn't verified |
| `ORPHAN` | Dead code | File not connected to build path |
| `SPEC_DRIFT` | Blueprint mismatch | Implementation doesn't match specification |
| `CHAIN_BREAK` | Merkle violation | Hash chain integrity compromised |

---

## Failure Log

Each failure is documented with date and iteration, what was attempted, why it failed, the pattern to avoid, and resolution.

---

### Failure #1: Genesis CONCEPT.md asserted "supported runtime" as present-tense product truth

**Date**: 2026-09-01
**Iteration**: 0
**Verdict ID**: RESEARCH_BRIEF GAP-DOC-01 (Round 1 verifier, verify-r1-docs)
**Category**: SPEC_DRIFT

#### What Was Attempted

The bootstrap `docs/CONCEPT.md` "Why" sentence described Agent Memory as including "the supported runtime that lets uncertain inference propose while only bounded authority creates durable consequence." The deep-audit reconnaissance then attributed that phrase to the README and graded the README/package contradiction HIGH.

#### Why It Failed

- Violation 1: the phrase does not appear in README.md; it was introduced by the genesis document itself (`docs/CONCEPT.md:5,23`), so the audit partly measured its own bootstrap.
- Violation 2: the package docstring, `reference/README.md`, and `run_conformance.py` all say "a reference, not a product" with conformance level 0; CONCEPT's present tense contradicts the shipped reality.

#### Pattern to Avoid

**Anti-Pattern**: Writing a genesis "Why" in the present tense for capabilities that are a forward objective, then hashing it into the ledger before the audit runs.

**Correct Pattern**: State forward objectives under "Forward Objective" (CONCEPT already has that section) and keep the "Why" to what the repository is today; when an audit follows a bootstrap, verifiers must check whether cited text originates in governance DNA written in the same session.

#### Resolution

| Status | Action Taken |
|--------|--------------|
| PENDING | Owner decision queued as Sprint 0 (GAP-DOC-01): either amend CONCEPT.md wording (new ledger entry, since the genesis hash covers it) or accept "supported runtime" as the 1.0 objective and reword the README badge instead. Severity lowered to MEDIUM in Round 1. |

#### Related Entries
- Ledger Entry: #1 (GENESIS)
- Audit Report: `docs/RESEARCH_BRIEF.md` GAP-DOC-01

---

### Failure #2: Recon over-graded three findings on grep-shaped evidence

**Date**: 2026-09-01
**Iteration**: 0
**Verdict ID**: RESEARCH_BRIEF Rounds 1-2 (GAP-SC-01, GAP-DOC-12, GAP-RT-08)
**Category**: HALLUCINATION

#### What Was Attempted

Phase 1 reconnaissance graded GAP-SC-01 HIGH ("coverage depends on whichever test happens to load them"), asserted GAP-DOC-12 ("feature families with no doc trail"), and asserted GAP-RT-08 ("zero references" to a Rust probe) from grep results without reading the consumers.

#### Why It Failed

- Violation 1: `fixture_conformance.py` runs all 64 fixtures and 23 of 34 scenario fixtures are loaded by named tests; the real hole is 10 fixtures.
- Violation 2: five of six "undocumented" families have a dedicated profile or program doc; the problem is index reachability (already GAP-DOC-04).
- Violation 3: the Rust probe is referenced by `uor-addr-compatibility.yml:49`.
- Violation 4 (added by Sprint 1 research, 2026-09-01): GAP-DOC-13 "phantom CLI subcommands" was graded MEDIUM, but `docs/CONFIGURATION.md:326` already states those commands are not implemented; the residual gap is a stale sketch missing `discover`. Downgraded to LOW.

#### Pattern to Avoid

**Anti-Pattern**: Grading a gap from the absence of a grep hit in one directory.

**Correct Pattern**: Open every consumer directory (tests, workflows, docs, wiki) before asserting "no reference"; Round 1-2 adversarial verification caught all three, which is the intended countermeasure (`SG-GrepShapedRunclaim-A`).

#### Resolution

| Status | Action Taken |
|--------|--------------|
| FIXED | GAP-SC-01 lowered to MEDIUM and narrowed; GAP-DOC-12 refuted and folded into GAP-DOC-04; GAP-RT-08 lowered to LOW. Recorded in the brief's Verification Log. |

#### Related Entries
- Ledger Entry: #1 (GENESIS)
- Audit Report: `docs/RESEARCH_BRIEF.md` Verification Log, Rounds 1-2

---

### Failure #3: Sprint 1 plan VETOed on a fail-open CI smoke, a false LD premise, and unreachable test branches

**Date**: 2026-09-01
**Iteration**: 1 (audit attempt 1 of 5 for this scope)
**Verdict ID**: AUDIT_REPORT 2026-09-01T22:40 VETO (V1-V7)
**Category**: SPEC_DRIFT (V2, V4-V6), HALLUCINATION (V2 research fact), COMPLEXITY_VIOLATION not triggered

#### What Was Attempted

`docs/plan-sprint1-install-correctness.md` proposed a wheel-install CI smoke of the form `python -c ... 2>&1 | grep -q ... && echo ...`, a Locked Decision LD7 asserting that `cli-doctor.yml` "only echoes" `pip install .`, and a `schema_dir()` resolver whose fallback branches were to be tested by monkeypatching a probe that the proposed code did not expose.

#### Why It Failed

- Violation 1: GitHub's default shell is `bash -e {0}` without `pipefail`; `-e` ignores non-final members of an `&&` list, so a missing schema let the step continue to `agent-memory --help` and pass. The solo audit pass predicted fail-always (assuming `pipefail`); the Option B reviewer found the true fail-open direction.
- Violation 2: `cli-doctor.yml:26` and `provider-discovery.yml:26` already run `pip install .`; the research grep pattern `pip install \.` could not match a line ending in ` .`, and the research brief repeated "0 workflows" against the deep-audit CI recon that had it right.
- Violation 3: two of four FX002 tests targeted branches with no seam.

#### Pattern to Avoid

**Anti-Pattern**: shell one-liners as CI acceptance tests; grep patterns anchored on trailing punctuation; tests written against branches the proposed code cannot expose; a plan author auditing their own citations solo.

**Correct Pattern**: acceptance smoke as an explicit Python snippet with a deliberate exit code per outcome; verify negative-space claims ("0 workflows do X") with a second pattern; expose probe seams as module-level names; honor `audit_risk_score` Option B (it caught the direction error).

#### Resolution

| Status | Action Taken |
|--------|--------------|
| PENDING | Governor amends plan text per AUDIT_REPORT V1-V7 and re-runs `/qor-audit` (attempt 2). |

#### Related Entries
- Ledger Entry: #3 (GATE TRIBUNAL)
- Audit Report: `.agent/staging/AUDIT_REPORT.md`

---

### Failure #4: Sprint 1 plan iteration 2 VETOed on a false masking mechanism and an unexecutable doc rule

**Date**: 2026-09-01
**Iteration**: 2 (audit attempt 2 of 5 for this scope)
**Verdict ID**: AUDIT_REPORT 2026-09-01T23:15 VETO (V1-V4)
**Category**: SPEC_DRIFT (V1 LD7 narrative, V2 rule, V4 affected files); coverage (V3)

#### What Was Attempted

The iteration-1 fix for LD7 corrected the grep-evidence but replaced one false narrative with another: "installing from the repository root lets `receipts.py:28` resolve the source `schemas/`". The stale-"Proposed" rewrite rule was generalised to "plus the date from the ADR header" without checking that three of the five headers carry no date, and the site list was compiled from the deep-audit count without a fresh grep.

#### Why It Failed

- Violation 1: an installed module lives in `site-packages`; `parents[2]/schemas` never points at the checkout, from any working directory (reproduced). The real masking is that the validate job's receipts-exercising steps import `reference/` directly and the console command never imports `receipts`.
- Violation 2: rule referenced data (dates) absent from three ADR headers; ADR-022 omitted from the list.
- Violation 3: `grep -rn "remains Proposed"` finds two more in-scope sites than the audit brief counted.

#### Pattern to Avoid

**Anti-Pattern**: fixing a citation's evidence while leaving its explanation unverified; writing a bulk rewrite rule instead of one sentence per site; inheriting counts from an earlier artifact without re-grepping at plan time.

**Correct Pattern**: when a Locked Decision explains a mechanism, reproduce the mechanism (here: import from the installed copy and print the resolved path) before locking it; enumerate doc edits site by site with the replacement text; re-run the discovery grep at plan time and reconcile with the brief.

#### Resolution

| Status | Action Taken |
|--------|--------------|
| PENDING | Governor amends per AUDIT_REPORT V1-V4 and re-runs `/qor-audit` (attempt 3; a third same-signature VETO routes to `/qor-remediate`). |

#### Related Entries
- Ledger Entry: #4 (GATE TRIBUNAL)
- Audit Report: `.agent/staging/AUDIT_REPORT.md`

---

### Failure #5: Sprint 1 plan iteration 3 VETOed on a transitive-import clause, a dangling doc pointer, and six undeferred stale sites

**Date**: 2026-09-01
**Iteration**: 3 (audit attempt 3 of 5)
**Verdict ID**: AUDIT_REPORT 2026-09-01T23:45 VETO (V1-V3)
**Category**: SPEC_DRIFT

#### What Was Attempted

LD7 was restated with "the console command never imports `receipts`" after reading `cli.py:9-16` only; a wiki replacement sentence pointed at "evidence above" without reading the page; the stale-site sweep used the literal "remains Proposed" and missed "should remain Proposed until", "until ADR-035 is accepted", and "Proposed ADR-030" phrasings.

#### Why It Failed

- `agentmem_ref/__init__.py:9` re-exports `receipts`, so any package import loads it; the true masking is laziness of `_validator`.
- `wiki-src/Runtime-Evidence.md` mentions isolation only on the line being replaced.
- Six same-class sites about Accepted ADRs remained, breaking the correct-or-defer rule from attempt 2.

#### Pattern to Avoid

**Anti-Pattern**: import-graph claims from a single file's import block; replacement prose with positional pointers ("above", "below") not checked against the page; stale-language sweeps keyed on one phrasing.

**Correct Pattern**: prove import claims with `sys.modules` after the real import; give replacements absolute pointers (a path); sweep with the ADR identifier crossed with "proposed" and then classify each hit as correct, fix, or defer.

#### Resolution

| Status | Action Taken |
|--------|--------------|
| FIXED | Iteration 4 amended all three grounds; audit attempt 4 (2026-09-02T00:20) PASSED with 0 violations from the independent reviewer. LD7's behavioral clause was proven by spy-wrapping `_validator` during the installed `--help` (zero calls). |

#### Related Entries
- Ledger Entry: #5 (GATE TRIBUNAL)
- Audit Report: `.agent/staging/AUDIT_REPORT.md`

---

### Failure #6: A test's import form was chosen from a comment's reasoning that was never run under the invocation it named

**Date**: 2026-09-06
**Iteration**: research (Loop 17, Sprint 3b)
**Verdict ID**: CI job 101516308032 on PR #386 (`FAILED (errors=1)`; `attempted relative import with no known parent package`)
**Category**: SPEC_DRIFT

#### What Was Attempted

#384 wrote `from .qualified_fixtures import ...` in `reference/tests/test_write_readable_visibility.py:20`, the only relative import under `reference/tests/`, with a comment asserting that an absolute `from tests...` import "only works under" `discover -t reference`.

#### Why It Failed

- The comment reasoned from module naming (`tests.X` vs `reference.tests.X`) and overlooked the file's own `sys.path.insert` at line 10, which makes `tests` importable under both. The absolute form works under every style; the clause was false.
- A third CI invocation exists: `discover -s reference/tests -p 'test_*.py'` with no `-t` (`evolveai-multicapability-qualification.yml:148`, `hermes-observe-govern-integration.yml:167`) loads tests as top-level modules, where no relative import can resolve.
- Both workflows are path-triggered and had not run on `main` since #384, so the defect stayed latent until PR #386 touched their paths.

#### Pattern to Avoid

**Anti-Pattern**: choosing an import form from reasoning about module names in a comment, without executing the candidate under each invocation style CI actually uses; treating "the targeted step and the umbrella step" as the complete set.

**Correct Pattern**: enumerate every `python -m unittest` line under `.github/workflows/`, reduce them to their distinct module-naming styles, and run the candidate under each before asserting which forms resolve. Follow the convention the sibling files already use unless a run proves it fails.

#### Resolution

| Status | Action Taken |
|--------|--------------|
| FIXED | Research brief section 1d ran both forms under all three styles. Plan `docs/plan-sprint3b-visibility-test-discover.md` (audit PASS, Entry #27, C1) applied the sibling convention and added `reference/tests/test_test_import_convention.py`, which fails on the relative form under every discover style. Sealed at Entry #28. |

#### Related Entries
- Ledger Entry: #26 (RESEARCH BRIEF, this branch)
- PR #386 (Sprint 3a branch): its ledger amendment records the CI run that surfaced this; that branch numbers its entries #26-#27 and will renumber on rebase

---

### Failure #7: A conversion was recorded as complete at the producer while the seam CI exercises stayed on the legacy route

**Date**: 2026-09-06
**Iteration**: research (Loop 18, Sprint 3c)
**Verdict ID**: PR #386 CI job 101516307796 (`provider-proof`: `assert report["correction"]["committed"] is True` -> AssertionError)
**Category**: SPEC_DRIFT

#### What Was Attempted

Sprint 2l (4b-1) gave `dashclaw_external_verdict` an `evidence_for` producer, tested at high risk to discharge under `evaluate_with_qualified_evidence` with a verified binding and an attestation. Sprint 2m (4b-2, Entry #24) then listed the module among the three that "present real evidence" and cross, and flipped `require_review` to fail closed.

#### Why It Failed

- No caller ever routed the producer's evidence: `commit_bound_mutation` still sets `review_satisfied=True` and calls `commit_proposal` without `evidence=`. After the flip that route parks. The seam neither forwards nor reports why it parked.
- The CI runner `run_dashclaw_external_verdict.py` and the workflow's inline invariant step both assert the approved correction commits, so a failed assertion produces no evidence file at all. The workflow is path-triggered and had not run since the flip.
- Forwarding the producer's evidence would not have been the fix: at medium risk both items are `artifact_bound` digests and would discharge as `delegated_policy` on binding and authority material alone -- the circularity the 4b-2 ruling rejected.

#### Pattern to Avoid

**Anti-Pattern**: declaring a module "converted" on the strength of a producer-level test while the compositional path that reaches the governed mutation is untouched; asserting outcomes in a CI runner rather than recording them, so the evidence disappears exactly when it matters.

**Correct Pattern**: DoD 20 applies per path, not per module -- enumerate the seams that reach `commit_proposal` and show each forwards or demonstrably parks. Runners record the outcome and assert on the record, and the workflow's inline invariants are derived from the runner's, not duplicated by hand.

#### Resolution

| Status | Action Taken |
|--------|--------------|
| FIXED | Plan `docs/plan-sprint3c-dashclaw-park-and-report.md` (audit VETO #30, PASS #31 with C1): runner, workflow invariants and runtime-evidence document assert the park; `test_dashclaw_correction_parks.py` names the laundering path and proves the seam does not take it. Sealed at Entry #32. |

#### Related Entries
- Ledger Entry: #29 (RESEARCH BRIEF)
- Ledger Entry: #24 (the classification this drift corrects)

---

### Failure #8: Sprint 3c plan iteration 1 VETOed on an unpassable test, an unreachable fixture state, a false unit-coverage claim, and an unaddressed assertion

**Date**: 2026-09-06
**Iteration**: 1 (audit attempt 1 of 5)
**Verdict ID**: AUDIT_REPORT_3c_attempt1 2026-09-06T13:50 VETO (V1-V4)
**Category**: SPEC_DRIFT

#### What Was Attempted

The plan specified the laundering-path test from the ladder's prose ("discharges as `delegated_policy`") without running it, named `review_discharge` for what `discharge_authority` carries, said "a fresh adapter" for a mutation whose `state_snapshot` presupposes a seeded state, stated from memory which test asserts `stale_authorization`, and enumerated the runner assertions to change from the lines that mention `committed` rather than from a run.

#### Why It Failed

- Every pre-audit lint passed: citations were all true. Truth of citations is not passability of tests.
- The author's empirical check ran after the plan was written and confirmed V1 independently; the Option B reviewer found V2-V4 by reading the adapter's stale check, grepping the claimed test, and reading the runner past line 338.

#### Pattern to Avoid

**Anti-Pattern**: specifying a test's exact assertion from doctrine prose or a dataclass field name without executing the path; naming which test covers a behaviour from recollection; scoping "which assertions change" by keyword instead of by running the runner and reading every failure.

**Correct Pattern**: run the candidate assertion before locking it (the field name is in the output); grep the claimed coverage; run the runner with assertions stripped and enumerate every assertion whose input changed.

#### Resolution

| Status | Action Taken |
|--------|--------------|
| FIXED | Plan iteration 2 amended V1-V4 and A1-A3 with every assertion executed before locking; audit attempt 2 (Entry #31) PASSED on independent re-review with zero grounds. |

#### Related Entries
- Ledger Entry: #30 (GATE TRIBUNAL, VETO)
- Audit Report: `.agent/staging/AUDIT_REPORT_3c_attempt1.md`

---

### Failure #9: Sprint 3d plan iteration 1 VETOed on an inverted red/green claim

**Date**: 2026-09-06
**Iteration**: 1 (audit attempt 1 of 5)
**Verdict ID**: AUDIT_REPORT_3d_attempt1 2026-09-06T19:20 VETO (V1)
**Category**: SPEC_DRIFT

#### What Was Attempted

The plan asserted which of its new tests would be red on `main` from the design of the fix (the resolvers will consult `receipts` seams, so patching those seams must change today's behaviour) rather than from today's code, which builds its source path from `REPO_ROOT` and never reads those seams.

#### Why It Failed

- The claim was reasoned forward from the intended implementation, not backward from the current one. Sprint 3c's Failure #8 was the same shape (an assertion locked without executing the path) one loop earlier.

#### Pattern to Avoid

**Anti-Pattern**: declaring red/green from the shape of the fix; treating "the test exercises the seam" as "the seam is what today's code reads".

**Correct Pattern**: run every new test against `origin/main` before locking which are red, and write the observed result into the plan.

#### Resolution

| Status | Action Taken |
|--------|--------------|
| FIXED | Iteration 2 closed V1 and A1-A4 (red/green observed, not inferred). Attempt 2 (Entry #39) VETOed on a new ground: the change-class rationale written into the header line, which the canonical parser rejects while the lenient gate writer accepts -- a header is data, not prose. Iteration 3 moved it below the header, verified with `parse_change_class`; attempt 3 (Entry #40) PASSED with no grounds. |

#### Related Entries
- Ledger Entry: #38 (GATE TRIBUNAL, VETO)
- Audit Report: `.agent/staging/AUDIT_REPORT_3d_attempt1.md`

---

### Failure #10: Sprint 4a plan iteration 1 VETOed on a misread seam, a numbering collision, a wrong feature id, and an asserted key that is never recorded

**Date**: 2026-09-06
**Iteration**: 1 (audit attempt 1 of 5)
**Verdict ID**: AUDIT_REPORT_4a_attempt1 2026-09-06T23:05 VETO (V1-V4)
**Category**: SPEC_DRIFT

#### What Was Attempted

An L3 contract plan written from the research brief's map of the surface: the adapter's evaluation selection was described from `governed_delete` and assumed identical in `commit_proposal`; the term home took the next doc number from memory; the layered-package feature id was recalled as FX020; the recall test named an `admitted` key from the `AdmissionResult` dataclass rather than the recorded per-candidate decision.

#### Why It Failed

- Two seams with the same shape were assumed to have the same branches; only one was read.
- Numbers (doc series, feature ids) were recalled, not listed.
- A test assertion was written against the dataclass a consumer sees, not the record the adapter emits.

#### Pattern to Avoid

**Anti-Pattern**: describing a second seam by analogy to the first; citing series numbers and ids from recollection; asserting on the wrapper's shape when the plan says "as recorded".

**Correct Pattern**: read every seam the plan factors; `ls` the series and `grep` the index before assigning a number or id; write assertions against the exact record the code produces.

#### Resolution

| Status | Action Taken |
|--------|--------------|
| FIXED | Iteration 2 closed V1-V4 and A1-A5 (the second seam read, the doc series listed, the index grepped, the assertion written against the recorded decision); attempt 2 (Entry #44) PASSED with seven plan-text advisories, applied. |

#### Related Entries
- Ledger Entry: #43 (GATE TRIBUNAL, VETO)
- Audit Report: `.agent/staging/AUDIT_REPORT_4a_attempt1.md`

---

### Failure #11: Sprint 4b plan iteration 1 VETOed because a faithful evaluation port left the runtime unable to commit, and the plan described the dead paths as unchanged

**Date**: 2026-09-07
**Iteration**: 1 (audit attempt 1 of 5)
**Verdict ID**: AUDIT_REPORT_4b_attempt1 2026-09-07T03:20 VETO (V1-V3)
**Category**: SPEC_DRIFT

#### What Was Attempted

A transcription of the PAMA table, floors, modifiers and envelope into the JS runtime, proven cell by cell by a Python-generated fixture (the transcription was verified: 65 cases, 0 mismatches). The plan then had `correct` park on every non-allowing outcome without porting any discharge, and wrote around the consequence: it kept the concurrency and error paths "as they are", promised committed receipts, and declared the Python contract version.

#### Why It Failed

- Every correction cell is non-allowing and an attestation discharges only the critical row, so a runtime with an evaluation and no discharge cannot commit a correction at all. The plan stated that in LD6 and contradicted it in LD2, the non-goals and FX025.
- The version claim came from the operator's "same contract" decision read as a field-name adoption rather than as the stages and compatibility semantics `docs/44` defines.
- A downstream implementer of the storage port (another repository) was not in the blast-radius reasoning.

#### Pattern to Avoid

**Anti-Pattern**: porting a control's decision half without its discharge half and describing the result as governed; declaring a contract version on the strength of field names; scoping blast radius to this repository when a port declares an interface others implement.

**Correct Pattern**: when a fail-closed change makes a path unreachable, say which tests and error codes die and who downstream is affected, and put the discharge route on the same plan or an explicitly ordered next one; a version claim is earned by implementing the contract's stages, not its names.

#### Resolution

| Status | Action Taken |
|--------|--------------|
| HELD | Operator ruled 2026-09-07: hold Sprint 4b, defer to a later research phase, proceed with Sprint 4c. The plan is marked HELD in place; no implementation started. |

#### Related Entries
- Ledger Entry: #47 (GATE TRIBUNAL, VETO)
- Audit Report: `.agent/staging/AUDIT_REPORT_4b_attempt1.md`

---

### Failure #12: Sprint 4c-1 plan iteration 1 VETOed on a record shape stated from one function and one branch

**Date**: 2026-09-07
**Iteration**: 1 (audit attempt 1 of 5)
**Verdict ID**: AUDIT_REPORT_4c1_attempt1 2026-09-07T06:30 VETO (V1-V3)
**Category**: SPEC_DRIFT

#### What Was Attempted

The plan described the audit-event shape from `_event` and assumed `_recall_event` matched; described the doctor report's keys from a grep of key names without their nesting; and closed the report's sub-objects from a single run on the composed fixture without a state directory.

#### Why It Failed

- Two builders with one purpose were assumed to share a shape; only one was read.
- A key list was taken from a flat grep rather than from a printed report.
- A schema was closed from one branch of a function with several.

#### Pattern to Avoid

**Anti-Pattern**: locking a record's shape from the first builder or the first branch observed; closing a schema (`additionalProperties: false`) over output the code produces conditionally.

**Correct Pattern**: print the record from each builder and each branch before locking its shape; close a schema only where the code has one shape, and say which branches were observed.

#### Resolution

| Status | Action Taken |
|--------|--------------|
| FIXED | Iteration 2 printed each record from each builder and branch before locking (recall events excluded; report keys nested as built; only invariant sub-objects closed); attempt 2 (Entry #50) PASSED with condition C1 applied. |

#### Related Entries
- Ledger Entry: #49 (GATE TRIBUNAL, VETO)
- Audit Report: `.agent/staging/AUDIT_REPORT_4c1_attempt1.md`

---

## Pattern Library (Extracted Lessons)

### Section 4 Razor Violations

| Anti-Pattern | Correct Pattern | Examples |
|--------------|-----------------|----------|
| 50+ line functions | Split at 40 lines | Pre-existing: 175 functions (GAP-RT-04), no failure entry yet |
| 4+ nesting levels | Early returns | Pre-existing: 22 functions (GAP-RT-04) |

### Security Patterns

| Anti-Pattern | Correct Pattern | Examples |
|--------------|-----------------|----------|
| Caller-asserted authority booleans on the base commit path | Derive from schema-validated evidence (pattern already in `reusable_grants.py:388-410`) | GAP-ARCH-04, GAP-SEC-02..04 (audit findings, not yet failures of an attempted fix) |

### Architecture Patterns

| Anti-Pattern | Correct Pattern | Examples |
|--------------|-----------------|----------|
| Present-tense capability claims in governance DNA | Forward objectives in their own section | Failure #1 |
| Grep-shaped "no reference" claims | Read all consumer directories | Failure #2 |
| Import-form claims reasoned from module names, unrun | Run the candidate under every CI invocation style | Failure #6 |
| Module declared converted on producer-level tests | DoD 20 per path: every seam forwards or demonstrably parks | Failure #7 |

---

## Failure Statistics

| Category | Count | Last Occurrence |
|----------|-------|-----------------|
| COMPLEXITY_VIOLATION | 0 | - |
| SECURITY_STUB | 0 | - |
| GHOST_PATH | 0 | - |
| HALLUCINATION | 2 | 2026-09-01 |
| ORPHAN | 0 | - |
| SPEC_DRIFT | 11 | 2026-09-07 |
| CHAIN_BREAK | 0 | - |

**Total Failures Recorded**: 12
**Failures Resolved**: 9 (Failure #2; Failures #3 and #4 grounds closed by the following iteration; Failure #6 fixed at Entry #28; Failure #8 grounds closed by iteration 2; Failure #7 fixed at Entry #32; Failure #9 grounds closed by iterations 2-3; Failure #10 grounds closed by iteration 2; Failure #12 grounds closed by iteration 2)
**Patterns Extracted**: 5

---

## Usage Notes

1. **Add entries when**:
   - /qor-audit returns VETO
   - Implementation fails Section 4 checks
   - Dead code is discovered
   - Any rejected approach

2. **Review entries when**:
   - Starting similar work
   - Seeing repeated violations
   - Onboarding new team members

3. **Extract patterns when**:
   - Same failure type occurs 3+ times
   - A clear anti-pattern emerges

---

*Shadow Genome maintained by The Qor-logic Judge*
*"Learn from failure to prevent its repetition."*
