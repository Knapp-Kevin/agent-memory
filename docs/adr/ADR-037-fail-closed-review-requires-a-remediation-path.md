# ADR-037: Fail-Closed Review Requires a Traversable Remediation Path

## Status

Accepted

Completes the authority leg opened by [ADR-004](ADR-004-pama-controls-mutation-authority.md) and closed in part by ledger entries #15 and #17. Depends on the ratification anchor sealed at entry #16.

## Context

`policy._apply_review` currently discharges `require_review` on `review_satisfied=True` plus any non-empty `approval_refs`. Both are caller-asserted. 51 call sites across 26 files rely on this.

Two of the three legs of this defect are closed. Self-approval is now derived from identity rather than trusted (entry #15), and `require_external_verification` can no longer be discharged by assertion at all (entry #17). The remaining leg is ordinary `require_review`, and the owner has determined it should fail closed.

**Fail-closed alone would deadlock an autonomous agent, and the escape hatches are not real.**

`_envelope` already names three permitted actions in every blocking outcome: `enter_pending_verification`, `collect_more_evidence`, and `defer`. Investigation found **no runtime consumes any of them**. They appear in `policy.py:281-289`, are mirrored in `domain_schema_mutation.py:38-44`, are mapped once in `enforcement_composition.py:58`, and are asserted in tests. No module acts on them. There is no parked state, no evidence-collection loop, and no defer-and-retry.

They are vocabulary, not machinery — and their absence is only harmless while assertion still discharges review. The moment it does not, a blocked autonomous caller has nowhere to go.

The one genuinely working route is a verified reusable grant discharging `require_review` through `evaluate_pama_with_reusable_grant`, made forgery-resistant at entry #16. But `ratify_reusable_grant` refuses self-ratification by construction, so an agent can only *use* a grant it already holds. It cannot obtain one at the moment it blocks.

**The remediation lifecycle already exists in one module.** `DurableDecisionRegistry.propose()` parks a proposal as `PENDING`; `commit(proposal_id, grant)` resumes it when authority arrives. Park, wait, resume on evidence. That is the fourth time this program has found a needed control implemented in one module and absent from the shared evaluator — after identity-derived self-approval, verified/unverified provenance, and the ratification registry.

## Decision

**Fail-closed is adopted for `require_review`, and does not take effect until the remediation path is traversable.** Sequencing is part of the decision, not an implementation detail: flipping 51 sites before `enter_pending_verification` is real would strand every autonomous caller, and that pressure becomes a workaround that outlives the control.

### 1. Sufficiency is a separation-of-parties test, not a human test

The governing invariant is **not** "a human must approve". It is **the proposer may not be the approver**. The codebase already enforces exactly this, and already admits non-human authority:

| Existing control | What it actually requires |
|---|---|
| `_apply_modifiers` derived self-approval (entry #15) | approver ≠ actor |
| `_grant_refusal:364` `self_approval_prohibited` | `grant.principal_id` ≠ `proposal.proposing_actor` |
| `_grant_refusal:378` `delegation_not_permitted_for_risk` | `DELEGATED_POLICY` — a **non-human** authority kind — is valid at low and medium risk |
| `_grant_refusal:372` `human_confirmation_required` | human confirmation required only at **high/critical** risk, or when the target was human-confirmed |

So agent-produced evidence is already a first-class authority source below high risk. This ADR generalizes that graduation into the shared evaluator rather than inventing a new rule.

**Agent-produced evidence may be of higher value than human ratification** where it is more direct, more reproducible, or more current. Provenance class is not a proxy for evidential quality. What matters is whether the evidence meets criteria appropriate to the circumstance, and the circumstance is already encoded as risk class.

### 2. Independence is the bar, and repetition is not independence

The one way this becomes authority laundering is a fleet manufacturing consensus by repeating itself. The repository already rejects that:

- `authority_laundering_harness.py:168` asserts `repetition_not_independent_corroboration` and holds `independent_corroboration` at `not_established` for a repeated observation.
- `autonomous_maintenance_harness.py:35-41` collapses a dependence group before cross-group fusion precisely so that "duplicate/derived/correlated observations [cannot] present themselves as independent evidence merely by increasing row count", with `row_count_is_not_corroboration` asserted.

**Independence is defined by evidential lineage and shared failure domains, not by agent identity.**

Distinct agents, models, providers, prompts, operators, or machines may *support* an independence claim. **None of them is sufficient by itself.** Two observations are independent only when no material common upstream observation, derivation path, state, or failure source could plausibly cause both to reach the same wrong conclusion. Correlated observations collapse into a single dependence group before anything is counted — which is precisely what `autonomous_maintenance_harness` already does.

**A second deterministic reproduction of the same test is validation of one evidence item, not a second evidence item.** Re-running a check confirms the check; it does not add a source. Treating it as a second evidence is counting hats, with more sophisticated hats.

Independence must therefore be established by lineage, never inferred from cardinality.

### 2b. Independence is necessary and not sufficient — agreement is not evidence

Independence defeats laundering by repetition. It does **not** establish correctness. Two genuinely independent parties can both be wrong, and a quorum of unqualified opinions remains opinion however uncorrelated it is. Counting agreement is not a substitute for checking anything.

The repository already draws this line, and it is the same line:

- `docs/24-determinism-probability-and-governed-uncertainty.md:41` — probabilistic discovery "may produce beliefs, rankings, hypotheses, candidates, confidence estimates, risk estimates, and proposed actions", while consequential behavior must occur inside an explicit governance envelope. Beliefs are inputs; they are not the envelope.
- `docs/24:140` — **"A deterministic threshold applied to a noisy estimate is not epistemic certainty."**
- `policy.py:8` — estimator confidence is an *input to* the decision; it never itself confers authority.

So a discharge requires evidence of a **checkable class**, not merely a separated party's assertion. **The classes are not equal, and are ranked:**

| Class | Standing |
|---|---|
| **Artifact-bound with a deterministic verifier** — a receipt, digest, committed fixture, qualification record | Satisfies an evidence criterion **directly** |
| **Reproducible procedure** — when inputs, method/version, result, and verifier are all bound | Satisfies an evidence criterion **directly** |
| **Calibrated estimator** — estimate carrying estimator identity, version, and calibration reference | **Weaker.** May *contribute* under explicit policy, particularly at low or medium risk. Must **never** itself become authority, and must **never** be the sole basis for discharging `require_review` |

The estimator ranking is not a new restriction. `policy.py:8` already makes estimator confidence an input to evidence quality with no path to the authority outcome; this records that it also cannot stand alone.

An assertion from a separated party in none of these classes is an opinion held at arm's length. It satisfies the independence bar and still fails here.

This has a consequence worth stating plainly, because it is the one that will be argued: **raising the count does not raise the class.** Ten independent unqualified assertions do not become one qualified evidence. If a discharge is failing for want of evidential class, the remedy is to produce checkable evidence, not to gather more agreement.

### 3. `enter_pending_verification` becomes a real parked state

Generalize `DurableDecisionRegistry`'s lifecycle: a proposal that cannot discharge parks with its decision, its unmet criteria, and its correlation identity, and is resumable when qualifying evidence arrives. Parking is a governed outcome that emits evidence, not a silent failure.

**A proposing actor may produce evidence for its own parked proposal. It may not certify that evidence, or decide that it discharges review.** Those are different acts and conflating them is an error. An agent that has been blocked should run the test, generate the receipt, produce the artifact, or perform the reproducible check — that is the system working. What it must not do is declare its own output sufficient.

**Resumption is an evaluator operation, not an actor operation.** It is triggered after qualifying evidence is admitted, and it re-evaluates policy from scratch. The proposing actor never holds the resumption decision. The existing invariant already expresses this correctly and is retained unchanged: the grant principal may not equal the proposing actor (`_grant_refusal:364`).

Self-produced evidence is permissible. Self-certified sufficiency is not.

### 4. `collect_more_evidence` must state what would discharge *this* proposal

Today an actor learns only that it is blocked. It must learn what would unblock it: which criteria are unmet, what class of evidence satisfies each, and what strength bar applies at this risk class. A remediation route an agent cannot compute is not a route.

*Amended by R5.* This section originally said "independence bar", which read as a count and had no referent. The bar is a **strength** ladder: the count is one at every risk class, and risk varies how strong that one group must be. Owned by step 3.

### 5. The parked state must not become a standing authority

A parked proposal carries no permission. Resumption re-evaluates against current policy and current state — it does not replay a decision made under earlier conditions. The staleness guard (entry #14) applies to resumption exactly as it applies to commit.

## Consequences

**Positive.** Autonomous operation survives fail-closed. Agent evidence is usable where the risk class permits, on stated criteria rather than provenance class. The escape hatches named since the first policy implementation stop being decorative.

**Costs, accepted.**

- Some proposals will park with plentiful agreement and no qualifying evidence. That is the control working, and it will feel like the control failing.
- 51 call sites must present real evidence or park. That is the point, and it is why the path lands first.
- Parked proposals are state that must be retained, bounded, and expired — retention is [#363](https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/363)'s domain, and this ADR adds to its load.
- Establishing independence is harder than counting approvals, and will sometimes conclude that plentiful evidence is one evidence.

**Risks.**

- **Authority laundering by fleet consensus** — the primary risk, mitigated by §2, which is doctrine the repository already holds and tests.
- **Parked-state pressure.** If parking is common, the fix is the criteria or the risk grading, not loosening the gate.

## The four variables, kept distinct

This is the conceptual model the rulings below enforce. It matters because collapsing any two of these is how governance becomes numerology.

| Variable | Question it answers |
|---|---|
| **Authority separation** | Who may approve? |
| **Evidence qualification** | What may justify approval? |
| **Independence** | When are multiple observations actually multiple? |
| **Risk** | How strong must all of the above be? |

They are four distinct axes. Keep them distinct, or Agent Memory eventually invents an `independent_verified_approver_count >= 2` boolean and nobody remembers six months later why governance turned into counting.

## Owner rulings

Recorded as decisions, not open questions.

**R1 — A proposing actor may produce evidence for its own parked proposal; it may not certify it.**
A blanket prohibition was proposed and is **rejected**: it conflates evidence *production* with *authority*. A blocked agent may run a test, generate a receipt, produce an artifact, or perform a reproducible check. It may not declare its own output sufficient. Resumption is a system/evaluator operation triggered once qualifying evidence is admitted and policy is re-evaluated. The durable-decision implementation already carries the correct invariant — the grant principal may not equal the proposing actor — and it is retained.

**R2 — Independence is defined by evidential lineage and shared failure domains, not by agent identity.**
Distinct agents, models, providers, prompts, operators, or machines may support an independence claim; none is sufficient alone. Two observations are independent only when no material common upstream observation, derivation path, state, or failure source could plausibly cause both to reach the same wrong conclusion. Correlated observations collapse into one dependence group. A second deterministic reproduction of the same test is validation of one evidence item, not a second one.

**R3 — Evidential classes are ranked, not equal.**
Artifact-bound evidence with a deterministic verifier satisfies an evidence criterion directly. A reproducible procedure does too, when inputs, method/version, result, and verifier are bound. A calibrated estimator is weaker: it may contribute under explicit policy, particularly at low or medium risk, but must never become authority and must never be the sole basis for discharging `require_review`.

**R6 — Conversion requires semantically relevant material; otherwise the proposal parks.** *(operator ruling, 2026-09-05, governing step 4b)*

> A caller converts only if it already possesses **semantically relevant** material that can **truthfully** populate an existing R3 qualifying class. **No new binding may be created merely because the migration requires one.** Otherwise the proposal parks.

"Has a digest" was reconnaissance, not the rule. R3 recognises two directly-satisfying classes — artifact-bound *and* reproducible procedure — so a digest was never the test. And checkability is necessary but not sufficient: the material must establish **the proposition under review**.

> **Evidence supports the proposition ≠ authority permits the consequence.**

**The tempting case, and why it fails.** `decision_overwrite`'s `AuthorityGrant` is unusually strong — bound to proposal, target, scope, actor, risk ceiling and lifetime, with `_grant_refusal` deterministic. It would classify beautifully as a reproducible procedure. **It answers the authority question, not the evidence question.** A perfectly valid grant can authorise review of a *bad* proposal, so it cannot also be proof that the proposal deserves discharge. Using it would collapse two of the four axes this ADR exists to keep apart.

**Descriptive records do not qualify.** A record stating "A became B, under authority X, for commit Y", with a verifier confirming it describes commit Y, establishes binding and integrity only:

> proposal says B → record says the proposal changes A to B → verifier confirms it does → therefore B is justified.

Circular. Qualifying evidence must **adjudicate** the transition: a rule that pre-exists the proposal, binding a canonical pre-state, the permissible resulting state, and the criterion, which the verifier re-runs against the actual proposed transition. A different value, a stale pre-state, a wrong target, or a forged result must refute.

**The test that decides any candidate pattern:**

> Can a caller create both the proposal **and** a matching fixture, after deciding what it wants, and satisfy the verifier?

If yes, it is laundering. If the evaluator resolves a pre-existing rule from a corpus the caller cannot write, it is sound.

**Verifier trust is evaluator-held.** A module may supply a verifier *implementation*; the evaluator owns the *registry* and decides which are trusted. No governed operation accepts a caller-supplied verifier mapping — registering your own verifier is certifying your own evidence.

**Authority stays outside the evidential proof**, in the receipt and `discharge_authority`, or in a separate attestation. It must not elevate the evidential class.

**R5 — Risk defines how strong, not how many.** *(operator ruling, 2026-09-05, resolving [#379](https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/379))*

§4 required stating "what independence bar applies at this risk class". Step 3 reported it as `undefined` because no such bar existed in accepted doctrine, and §2b and line 128 of this ADR both argue against inventing a count.

**The count is one at every risk class.** What is required is the *existence* of one qualifying independent dependence group — R2's lineage grouping already defines what one group is. That does not vary by risk and is not a number to be tuned. **Risk varies the strength that one group must reach:**

| Risk | Authority kind | Qualification class | Binding status |
|---|---|---|---|
| low | `delegated_policy` or `human_confirmation` | directly-satisfying; a calibrated estimator may contribute | `asserted` |
| medium | `delegated_policy` or `human_confirmation` | directly-satisfying; a calibrated estimator may contribute | `asserted` |
| high | `human_confirmation` only | directly-satisfying only | **`verified`** |
| critical | `human_confirmation` only | directly-satisfying only | **`verified`** |

**Two of these three rows are pre-existing implemented doctrine, and one is new.** Saying which is which matters, because presenting all three as novel would overstate the ruling and presenting the new one as pre-existing would smuggle a ruling in as a restatement.

- **Authority kind — pre-existing.** `policy.attestation_refusal` already requires `human_confirmation` when `risk_class in _HIGH_RISK`, and `decision_overwrite._grant_refusal` already returns `delegation_not_permitted_for_risk` above medium.
- **Qualification class — pre-existing.** R3 already says a calibrated estimator "may contribute under explicit policy, particularly at low or medium risk", never authority and never a sole basis.
- **Binding status — new.** R3 speaks of artifact-bound evidence "with a deterministic verifier", which presumes the verifier works; step 2 then split `asserted` (a verifier is named) from `verified` (one ran and passed). Requiring `verified` at high and critical makes the **evidence** axis as strict as the **authority** axis already is, at the same risk classes.

**What is in force today.** The ladder is what step 4 will enforce. Only one row bites now: the authority kind on the `require_external_verification` path, via `attestation_refusal`. `_apply_review` still discharges `require_review` on `review_satisfied` plus `approval_refs` at any risk class with no authority-kind check — and `require_review` occupies nine base-table cells at high or critical risk. The §4 report marks each row in force or pending accordingly, because stating a bar the system does not enforce is the defect step 3 was corrected for.

**R4 — `delegated_policy` at medium risk requires one separated, properly authorized principal, not two.**
The principal still needs qualifying evidence and valid scope/risk authority. Requiring two by default would quietly rebuild the quorum model §2b exists to reject. The `minimum_independent_human_evidence >= 2` rule in `reusable_grants` has a **different job**: it governs the creation of *reusable authority from historical precedent*, followed by a separate ratification transition. It must not be generalized into a two-approver requirement for ordinary review.

## Implementation order — rigid

The gate does not close until the first three exist. This ordering is part of the decision.

1. **Parked proposal state** — `enter_pending_verification` as a real, resumable, evidence-emitting outcome. **DONE** (Loop 8, ledger entry #18): `reference/agentmem_ref/core/pending_verification.py`.
2. **Evidence qualification and dependence lineage** — R2 and R3 made computable, including dependence-group collapse. **DONE** (Loop 9, ledger entry #19): `reference/agentmem_ref/core/evidence_qualification.py`.
3. **Governed resumption and re-evaluation** — evaluator-owned, policy re-evaluated from scratch, staleness applied. **Also owns §4**. **DONE** (Loop 10, ledger entry #20): `reference/agentmem_ref/core/resumption.py`.
4. **Fail-closed `require_review`** — convert the 51 caller sites. **This step splits**, because the sequencing principle above applies recursively:

   - **4a — the discharge path.** **DONE** (Loop 12, ledger entry #22): `policy.evaluate_with_qualified_evidence`. Measured before it was built: *no* entry point in `policy` discharged `require_review` on qualified evidence — `evaluate` and `evaluate_with_base_outcome` take no evidence, and `evaluate_with_external_verification` early-returns unless the outcome is `require_external_verification`. Flipping the gate first would therefore have left all 51 sites refused with **no route** — the exact halt this ADR forbids. Additive: `_apply_review` untouched, both paths coexist.
   - **4b-1 — migrating the evidence producers.** **DONE** (Loop 13, ledger entry #23). The axis governing conversion is not test-versus-production but **whether a module already holds a digest or reproducible procedure**. Measured across the seven modules that set `review_satisfied=True`: `procedural_memory`, `dashclaw_external_verdict` and `reusable_grants` can produce genuine artifact-bound evidence; `decision_overwrite`, `forbidden_hits`, `visibility_characterization` and `benchmark_security` hold only a name. The first three are migrated, additively. **For the other four, conversion would mean inventing an `artifact_ref` and `digest` to satisfy the classifier — the caller-asserted defect dressed as a migration — so this ADR's own ruling applies: they present real evidence or they park.** Which of those, is an operator decision, raised rather than assumed.
   - **4b-2 — the flip and the conversion.** **DONE** (Loop 14, ledger entry #24). `review_satisfied=True` plus arbitrary `approval_refs` no longer discharges `require_review`. Three sites cross with real evidence; **four park** — `decision_overwrite` low/medium, `forbidden_hits`, `visibility_characterization`, `benchmark_security` — under R6, because none possesses material establishing the proposition under review. `decision_overwrite` high keeps its external-verification semantics unchanged.

**Step 4 is complete, and with it this ADR is enforced rather than described.**

*What the flip required, discovered during implementation and disclosed.* After removing the asserted route, **no governed entry point could present evidence**: `commit_proposal`, `governed_delete`, `evaluate_crossing`, `import_bundle`, `evaluate_source_notice`, `purge`, `propose_rebuild` and `evaluate_pama_v13` all evaluated directly. Their callers would have had a remediation path in doctrine and no way to reach it — the dead end this ADR prohibits. Each gained an `evidence`/`attestation` channel, and every wrapper that forwards to one (`configured_restart`, `restart_runtime`, `runtime_composition`, and the subclass adapters) forwards it too: **no path capable of reaching a governed mutation may bury the capability one layer up.** A probed hard flip breaks **55 tests across ~30 files**, and they are two different kinds of work: a minority assert the gate's own behaviour and are genuine declared amendments; the majority use assertion as *scaffolding* to reach unrelated behaviour and must be given real qualified evidence instead — amending those would silently delete coverage rather than update it.

**What step 1 settled, so steps 2–3 do not re-litigate it.** Two questions surfaced in audit and were decided:

- **Which outcomes park.** Only `require_review` and `require_external_verification` — refusals that granted a route. `allow`/`allow_with_ledger` are refused because nothing was refused; `block` is refused because `_envelope` names `enter_pending_verification` in its *prohibited* set, so parking one would contradict the recorded envelope and create a record no evidence could ever discharge.
- **What the record retains.** The whole `Proposal`, not an identity summary. Step 3 must re-evaluate from scratch and `policy.evaluate` takes a `Proposal`; retaining it is also what carries `state_snapshot` forward so the staleness guard can be applied at resumption. The record shape is therefore fixed and step 3 does not reshape it.

The registry has **no** `resume` method — not a stub, not one raising. Step 3 adds it, and step 3 is gated on step 2.

**What step 2 settled.**

- **§4 belongs to step 3.** As written, this ADR's four-step order named no owner for §4 (`collect_more_evidence` must state which criteria are unmet, what class satisfies each, and what independence bar applies at this risk class). It is not step 2's: computing "what independence bar applies at this risk class" needs a risk class, and the qualification module deliberately refuses one so it cannot return a sufficiency verdict. It lands in **step 3**, which already re-evaluates against a risk class and already holds the parked record that would carry the message. Recorded here so the requirement is owned rather than falling between four cycles that each correctly declared it out of scope.
- **Qualification is derived, and it is not yet verification.** A class comes from which bindings an item carries, never from a claim it makes. But the bindings are themselves caller-supplied strings, so every class pairs with a binding status: `asserted` (nobody has checked), `verified` (a verifier in the evaluator's registry ran and passed), `refuted` (it ran and failed). `refuted` is distinct on purpose — collapsing it into `asserted` would make a failed check indistinguishable from an unmade one. **This does not close the caller-asserted-input pattern**; it makes evidence a typed claim that names its own verifier.
**What step 3 settled.**

- **Resumption's range is narrower than this ADR implies, and the reason is step 4.** Measured: `require_external_verification` is resumable through a bound, separated attestation. `require_review` is **not** — evidence reaches the evaluator only as `proposal.evidence_refs`, and M-EVID is an emptiness check, so appending qualified, independently verified evidence changes nothing. Its only discharge today is `review_satisfied` + `approval_refs`, which is exactly the assertion route step 4 converts. That is what the ordering means, not a shortfall. The §4 report therefore names step 4 as the blocker rather than listing an evidence criterion no evidence can satisfy — **telling an agent to collect evidence that cannot help is worse than telling it to wait**.
- **§4's independence bar has no referent, and this cycle refused to invent one.** No bar exists in accepted doctrine: the only count threshold is `reusable_grants`' `>= 2`, which R4 forbids generalizing, and line 128 of this ADR warns by name against inventing `independent_verified_approver_count >= 2`. The report states `bar: undefined` with the open question attached, and the question is filed rather than answered in an implementation cycle.
- **Separation is not re-derived.** `evaluate_with_external_verification` already calls `attestation_refusal` internally and surfaces the result in `decision.reasons`, so resumption reads the refusal from the decision. A second copy of a control already correctly placed in the shared evaluator is two things that can diverge.
- **Admitted evidence amends `evidence_refs` and nothing else.** A resumption that could rewrite `risk_class` or `actor_id` would be a proposal-rewriting primitive, which is an authority bypass rather than a wrong shape.

- **Independence is three relations, not two.** Derivation edges and shared failure domains are both insufficient alone: two runs of one deterministic procedure share neither, and R2 says in as many words that they are one evidence item. Identical `(method, method_version, inputs)` is the third relation. A declared failure domain may only **merge** groups, never split one — the constrained party can weaken its own independence claim and never strengthen it.

Do not flip the gate before 1–3 exist. A control whose remediation path does not yet work is a halt, and the pressure it creates becomes a workaround that outlives it.

## Related

- Ledger entries #14 (staleness on delete), #15 (derived self-approval), #16 (ratification anchor), #17 (external verification requires attestation)
- [#362](https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/362) public API boundary — the parked-state type is a public contract
- [#363](https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/363) production state profile — parked proposals are retained state
