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

---

## Failure Statistics

| Category | Count | Last Occurrence |
|----------|-------|-----------------|
| COMPLEXITY_VIOLATION | 0 | - |
| SECURITY_STUB | 0 | - |
| GHOST_PATH | 0 | - |
| HALLUCINATION | 2 | 2026-09-01 |
| ORPHAN | 0 | - |
| SPEC_DRIFT | 5 | 2026-09-06 |
| CHAIN_BREAK | 0 | - |

**Total Failures Recorded**: 6
**Failures Resolved**: 4 (Failure #2; Failures #3 and #4 grounds closed by the following iteration; Failure #6 fixed at Entry #28)
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
