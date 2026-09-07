# Plan: Sprint 2m — the fail-closed flip

**change_class**: feature
**Risk Grade**: L3 (top of the scale; see below)
**Session**: 2026-09-05T0700-ac3145
**Research**: `docs/research-brief-sprint2m-fail-closed-flip-2026-09-05.md`
**Iteration**: 5 (operator sanction of mechanical completion, with DoD 20)
**Implements**: ADR-037 **step 4b-2**, under the operator ruling of 2026-09-05

## Objective

`review_satisfied=True` plus arbitrary `approval_refs` stops discharging `require_review`. Three sites cross with real evidence. Four park. ADR-037 becomes enforced rather than described.

## The governing rule

Recorded as **ADR-037 R6**, because it supersedes the working classification Loop 13 used:

> A caller converts only if it already possesses **semantically relevant** material that can **truthfully** populate an existing R3 qualifying class. No new binding may be created merely because the migration requires one. Otherwise the proposal parks.

"Has a digest" was reconnaissance. R3 recognises two directly-satisfying classes, so a digest was never the test — and checkability is necessary but not sufficient. The material must establish **the proposition under review**.

> Evidence supports the proposition ≠ authority permits the consequence.

## LD0 — Semantic relevance is a design judgement, never a runtime field

**This is the decision most likely to be implemented wrongly, so it is stated first.**

The obvious way to "implement" R6 is a `relevance` or `establishes` attribute on `EvidenceItem`. That would be the caller-asserted defect for the **eleventh** time, and worse than the ten before it: the assertion would be about *meaning*, which nothing can check, in a control whose whole purpose is to stop unverifiable claims discharging decisions.

R6 is applied by **choosing which sites convert and recording why**. The code gains no relevance concept, no new field, and no new enum value. DoD 12 asserts this by diff.

## LD10 — The entry-point evidence channel, as sanctioned (operator ruling)

Implementation surfaced that after the flip **no governed entry point could present evidence**: `GovernedMemoryAdapter.commit_proposal`, `crossing.evaluate_crossing`, `interchange.import_bundle` and `evaluate_source_notice` all called `policy.evaluate` directly. Their callers would have had a remediation path in doctrine and no way to reach it — the dead end ADR-037 prohibits.

The operator sanctioned the channel **with one boundary change**:

| | Ruling |
|---|---|
| `evidence=` | **yes** — pertinent to that exact proposal; empty/default parks normally |
| `attestation=` | **yes** — where the existing authority path permits, still subject to the shared evaluator's binding and separation checks |
| `verifiers=` as a caller-supplied mapping | **no** |

**Why the mapping is refused, and it is the important half.** PR #383 established that a module may supply a verifier *implementation* while the evaluator owns the *registry*. A per-call mapping hands registration back to the caller:

```python
commit_proposal(..., verifiers={"thing": lambda item: True})
```

That is `review_satisfied=True` rebuilt with more Python. Verifier trust moves to an **evaluator/host-owned `VerifierRegistry`**, configured on the adapter/runtime rather than passed per operation.

**Further rules, all binding:**

- **No authority laundering across systems.** `import_bundle` must not treat sender export authority as evidence sufficient for receiver authorisation — existing doctrine already says the sender's crossing receipt is never reused as the receiver's allow decision. A source lifecycle notice establishes that the remote source changed; it does not grant local correction or deletion authority.
- **Forwarding surfaces are audited too.** `configured_restart`, `restart_runtime` and `runtime_composition` wrap or delegate `commit_proposal`. Adding the channel only at the base adapter leaves a dead end one layer up.
- **Evidence never modifies `review_satisfied` or `approval_refs`.** Those are legacy migration state. Qualified discharge stays its own path.

## LD11 — The fixture must adjudicate the transition, not describe it (operator ruling)

My change-record pattern is **rejected as written**, and the reasoning is the part to keep. A record saying *"A became B, under authority X, for commit Y"*, plus a verifier proving the record accurately describes commit Y, establishes **binding and integrity**. It does not establish that A *should* become B:

> proposal says B → fixture says the proposal changes A to B → verifier confirms it really does → therefore changing A to B is justified.

Circular. Neatly hashed, still circular.

**The sound shape** is an **expected-transition fixture that exists independently of the proposal**, resolved by the evaluator from a trusted corpus. It binds:

- the canonical **pre-state** or state version,
- the **permissible or expected** resulting state / invariant,
- the **criterion** being evaluated.

The verifier reruns that rule against the actual proposed transition. A different proposed value, a stale pre-state, a wrong target, or a mismatched transition must **refute**. That is R3's `reproducible_procedure` — inputs, method, method version, result, verifier — which R3 already recognises as directly satisfying.

**Authority stays outside the evidential proof.** "On whose authority" belongs in the receipt, in `discharge_authority`, or in a separate attestation. It must not elevate the evidential class, or authority merges back into evidence two loops after they were separated.

**The adversarial test that decides the pattern:**

> Can a malicious caller create both the proposal **and** a matching fixture after deciding what it wants, then satisfy the verifier?

If yes, the pattern is laundering and is rejected. If the evaluator resolves a **pre-existing** rule from a trusted corpus and the caller can only present a proposal against it, the pattern is sound. **DoD 14 makes this an executable test, not a principle.**

## Boundaries

**In scope**: the flip; four sites park; the 58 affected tests reclassified.

**Explicitly out of scope, and unchanged:**

| Unchanged | Why |
|---|---|
| `_apply_review`'s `require_external_verification` cap (Loop 7) | the flip is about assertion discharging `require_review` |
| `evaluate_with_external_verification` and its early return | `decision_overwrite` high and every external-verification path keep current semantics |
| `evaluate_with_qualified_evidence` (Loop 12) | the three producers continue through it |

## Design decisions

**LD1 — The flip is one line, and it refuses by naming what is missing.**
`_apply_review`'s final `return ALLOW_WITH_LEDGER, [...]` becomes a refusal carrying `review_requires_qualified_evidence`. Not a bare refusal: criterion 7 requires the caller to learn what would unblock it, and Loop 12 already built per-axis reasons.

**LD2a — The four sites are connected to the parking machinery (audit V1).**

Iteration 1 claimed the four sites were "not modified — they park because policy changed". Measured, that is false: `decision_overwrite:192-208` selects `NO_ACTION` when the operation is absent from `permitted_actions`, and **no site references `PendingVerificationRegistry` or calls `.park(`**. An unmodified site gets a clean refusal, which is better than a crash and is **not the parked state** — no `ParkedProposal`, no `memory.pending_verification` event, and nothing for `criteria_for` to report on, leaving DoD 7 with nothing to read.

The operator's criterion distinguishes them by name: *park* rather than *fail*. Flipping the gate and leaving four production paths at a clean dead end is the halt ADR-037 spent three cycles avoiding.

**The connection is already authorised.** `_envelope` returns, for `REQUIRE_REVIEW`, permitted actions `("enter_pending_verification", "collect_more_evidence", "defer")`. **`enter_pending_verification` is permitted.** A refused module parking its own proposal is the actor taking exactly the remediation the envelope grants it — not an overreach. Step 1 built the registry for this and nothing has called it since.

So the four sites **are** modified, to park when refused. That is not giving them evidence and does not touch R6: it gives them the route ADR-037 always intended, and it is what makes "park rather than fail" true rather than aspirational.

**LD2b — "Park" means two different things, because the four sites are two different shapes (audit V3).**

Measured:

| Module | Classes | Module-level fns | Nature |
|---|---|---|---|
| `decision_overwrite` | 5 | 0 | **stateful production path** — `DurableDecisionRegistry` holds a lifecycle across calls |
| `forbidden_hits` | 3 | 16 | executable **assertion harness** (#148) |
| `visibility_characterization` | 0 | 11 | executable **characterization** (#308) |
| `benchmark_security` | 0 | 11 | **benchmark/scorecard** harness |

**For `decision_overwrite`, parking must be durable.** A `PendingVerificationRegistry()` constructed inline would die at the end of the call: a `ParkedProposal` would exist and an event would fire, satisfying a naive DoD, while **no record survives for `criteria_for` to read and nothing can ever resume**. A parked record that outlives no call is a no-op with an event attached. The registry is held by `DurableDecisionRegistry` alongside its existing state, as the substrate and adapter already are. That module is also the one Loop 8 generalised the parking lifecycle *from*, which makes an ephemeral park there particularly incongruous.

**For the three harnesses, the opposite.** They exist to demonstrate behaviour, and what they must now demonstrate is that their proposal parks. Giving each persistent injected lifecycle state would be building a registry into a scorecard. For them, constructing a registry, parking, and **reporting the parked outcome in their output** is correct and complete — the record is the observation.

**LD2 — The four sites park, and none of them is given evidence.**

The operator ruled each individually, and the reasoning is recorded because it is the part that generalises:

| Site | Ruling | Why the tempting material does not qualify |
|---|---|---|
| `decision_overwrite` low/medium | park | `AuthorityGrant` is unusually strong — bound to proposal, target, scope, actor, risk ceiling and lifetime, with `_grant_refusal` deterministic. **It answers the authority question, not the evidence question.** A valid grant can authorise review of a bad proposal, so it cannot also prove the proposal deserves discharge |
| `forbidden_hits` correction | park | executable observations and a fixture matrix establish forbidden-hit *lifecycle behaviour*, not the truth of "Thursday → Friday". Reusing them would be **evidence-purpose laundering** |
| `visibility_characterization` correction | park | its observations establish whether a *committed* change becomes readable correctly. Using post-consequence visibility evidence as pre-consequence review evidence is circular |
| `benchmark_security` permanent deletion | park | the hard gates produce checkable results about escape rate, residue and stale authorisation — governance properties of the system, not why *this* deletion is warranted |

`decision_overwrite` high is untouched: it already resolves to `require_external_verification`, measured, and the ruling forbids gratuitously rewriting that path.

**LD3 — Test reclassification is per-test, marked, and counted (audit V2).**
Criterion 6. Each of the 58 changed tests is labelled **expected semantic change** or **actual regression**, in the test itself. A regression is a defect to fix, not an expectation to update.

Iteration 1 proposed to assert this "by the absence of any bulk-rewritten expectation", which names no mechanism — and with 23 files going red, the pressure to sweep peaks exactly where the check was weakest.

**Made mechanical**: every test whose expectation changes carries a marker naming its classification and this cycle (`ADR-037 step 4b-2: expected semantic change` / `... actual regression`), and a meta-test asserts **the marker count equals the count of changed expectations**. A sweep then fails visibly instead of passing quietly. Loop 11's advance commitment worked for the same reason: it was falsifiable.

**LD4 — Scaffolding tests split; they are not bypassed.**
Where a test used assertion to reach later behaviour, the concern splits: one test proves the production call now parks without evidence, and a separate scenario supplies genuine qualified fixture evidence **only where the fixture actually establishes the proposition being reviewed**. No test-only bypass, no `_test_discharge` seam.

**LD5 — Where no honest fixture exists, the scenario stays blocked.**
The later-stage scenario is redesigned or left blocked, and said so in the test. It is not grandfathered through assertion. This is the door the operator closed in advance and it is the one most likely to be pushed on when the suite is red.

**LD6 — The baseline is not the goal.**
1071 green is not a target. The invariants are. Some outcomes that were green were obtained through the discharge path being removed, and their changing is the point rather than a cost.

## Affected files

| File | Change |
|---|---|
| `reference/agentmem_ref/policy.py` | **modified** — `_apply_review` no longer discharges `require_review` on assertion |
| `docs/adr/ADR-037-...md` | **modified** — R6 recorded; step 4b-2 marked done |
| `decision_overwrite.py`, `forbidden_hits.py`, `visibility_characterization.py`, `benchmark_security.py` | **modified** — park on refusal (LD2a), taking the `enter_pending_verification` the envelope already permits |
| ~23 test files | **modified** — per-test reclassification, each marked |

**No production module is given invented evidence.** The four are modified only to *reach* the parking machinery — not to acquire bindings, and not to change what policy decides about them.

## Feature Inventory Touches

| ID | Feature | Disposition |
|---|---|---|
| FX017 | `require_review` fails closed: assertion no longer discharges it | NEW |
| FX009 | Review discharge provenance | MODIFIED — the asserted route is removed |

## Definition of Done

Mapped to the operator's acceptance criteria.

1. **`review_satisfied=True` plus arbitrary `approval_refs` can no longer discharge `require_review`** — asserted directly, at low and medium risk.
2. **The three 4b-1 producers continue through `evaluate_with_qualified_evidence`** and still discharge.
3. **The four non-qualified sites demonstrably park** — asserted per site, and asserted *against failing*: no exception escapes and no mutation is committed (LD2a).
3a. **`decision_overwrite` parks durably** (LD2b): the parked record is **retrievable from the registry after the call returns**, and `criteria_for` on it names the unmet criterion. An inline registry fails this.
3b. **The three harnesses report the parked outcome in their output** (LD2b): the parked decision and its unmet criteria appear in the matrix/characterization/scorecard each produces, rather than the run silently losing the case.
4. **External-verification behaviour is unchanged** — `decision_overwrite` high, and `evaluate_with_external_verification`'s early return, asserted identical to pre-flip.
5. **No new digest, `artifact_ref`, producer/principal field, or verifier exists solely to satisfy migration** — asserted over `EvidenceItem`'s fields, and by diff of the four parking modules: their **only** change is the park connection, with no binding, digest or evidence construction added.
6. **Every changed test is classified** as expected semantic change or actual regression, marked in the test itself, naming this cycle. **A meta-test asserts the marker count equals the count of changed expectations** (LD3, audit V2), so a mass snapshot update fails visibly rather than passing quietly.
7. **Parking exposes the exact missing evidence class/status** — `criteria_for` on a parked record from each of the four sites names the unmet criterion and its bar.
8. **Full suite and adversarial negatives green before merge.**
9. `_apply_review`'s external-verification cap is byte-identical (LD-boundary).
10. The asserted route is gone from the *code*, not merely from the tests: no path returns `ALLOW_WITH_LEDGER` from `_apply_review` for `require_review`.
11. Loop 12's `test_the_asserted_route_itself_is_untouched` and Loop 13's equivalent are **inverted as declared amendments**, naming this cycle.
12. **`EvidenceItem` gains no relevance concept** (LD0): no `relevance`, `establishes`, `purpose`, or `semantic_*` field, asserted over its dataclass fields.
13. Validators clean; no schema modified.
14. **The laundering test** (LD11): a caller that fabricates both a proposal and a matching rule, after choosing its desired outcome, **does not** satisfy the verifier — because the rule is resolved from an evaluator-held corpus the caller cannot write. Asserted directly, as the test that decides whether the fixture pattern is sound.
15. **No caller-supplied verifier mapping exists** on any governed entry point (LD10): asserted over the signatures of `commit_proposal`, `evaluate_crossing`, `import_bundle` and `evaluate_source_notice`.
16. **Verifier trust is evaluator-held**: a `VerifierRegistry` configured on the adapter/runtime, and registering into it is not reachable from a proposal or its evidence.
17. **Forwarding surfaces carry the channel** (LD10): `configured_restart`, `restart_runtime` and `runtime_composition` are not dead ends one layer above the adapter.
18. **A stale pre-state, a wrong target, or a mismatched transition refutes** (LD11), asserted per case — the properties that make the rule adjudication rather than description.
19. **Evidence does not modify `review_satisfied` or `approval_refs`**, asserted by comparing the proposal before and after a qualified commit.
20. **No unreachable capability** (operator, 2026-09-05). *Every public or compositional path capable of reaching a governed mutation must either forward qualified evidence/attestation or demonstrably park.* There is no third category in which the capability exists underneath but is buried by a wrapper. Asserted by enumerating the wrapping/delegating surfaces — `configured_restart`, `restart_runtime`, `runtime_composition` — and checking each either forwards the channel or parks, with a test that fails if a new wrapper appears without one.

## CI Commands

```
python -m unittest discover -s reference/tests -t reference
python scripts/validate_schemas.py
python scripts/validate_fixtures.py fixtures
```

## Rollback

Revert `policy.py`'s one-line change, the four park connections, and the test reclassifications.

## Next

`/qor-implement`. Audit attempt 3 returned PASS with no further conditions.

Attempts 1 and 2 vetoed on V1-V3: the four sites were refused rather than parked and the plan contradicted itself about whether they were modified (V1); DoD 6 named no mechanism for the criterion most likely to be quietly violated (V2); and the four were treated as one shape when they are two, which would have made parking ephemeral in the production path and over-built in three harnesses (V3). All three are discharged.
