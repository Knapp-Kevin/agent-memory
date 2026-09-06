# Research Brief: Sprint 2i — governed resumption and re-evaluation

**Date**: 2026-09-05
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 10.
**Implements**: ADR-037 implementation order **step 3 of 4**, plus **§4**, which step 2 assigned here.

## 1. Scope

Step 1 gave a refusal a place to sit. Step 2 gave evidence a class and a lineage. Step 3 is the first step that **consumes** both, and the first that produces a state transition rather than a description.

| Step | Status |
|---|---|
| 1. Parked proposal state | done, entry #18 |
| 2. Evidence qualification and dependence lineage | done, entry #19 |
| 3. Governed resumption + §4 messaging | **this cycle** |
| 4. Fail-closed `require_review` | **not built.** `policy._apply_review` untouched; the 51 sites unconverted |

Step 4 remains out of scope. After this cycle all three prerequisites exist, so step 4 becomes *permissible* — that is the point of the ordering — but it is a separate cycle with its own audit, and it converts 51 call sites.

## 2. A finding that needs an owner ruling before §4 can be fully honest

ADR-037 §4 requires `collect_more_evidence` to state three things: which criteria are unmet, what class of evidence satisfies each, and **"what independence bar applies at this risk class."**

**No such bar exists in accepted doctrine.** The search is exhaustive:

- The only independence count threshold anywhere in the reference runtime is `reusable_grants.minimum_independent_human_evidence >= 2`, and **R4 explicitly forbids generalizing it**: it "governs the creation of *reusable authority from historical precedent* … It must not be generalized into a two-approver requirement for ordinary review."
- `docs/33-pama-decision-table.md` grades outcomes by risk. It says nothing about how many independent evidence groups any outcome needs.
- §2b argues *against* counting: "raising the count does not raise the class… Ten independent unqualified assertions do not become one qualified evidence."
- And ADR-037:128 names the exact mistake by name: *"Keep them distinct, or Agent Memory eventually invents an `independent_verified_approver_count >= 2` boolean and nobody remembers six months later why governance turned into counting."*

So §4 asks the system to state a bar that the same ADR warns against inventing. **This cycle will not invent one.** Step 3 states the criteria that genuinely exist and reports the independence bar as **undefined**, naming it as an open doctrine question rather than silently omitting it or fabricating a threshold. The question goes to the operator as an ADR amendment proposal.

That is not a gap in the work; a message that says "this criterion has no defined bar" is more useful to an agent than a confidently invented number, and far more useful than silence.

## 3. What *is* derivable, and it is more than expected

Four of §4's criteria have real referents in accepted, implemented doctrine:

**Qualification class (R3).** Step 2 computes it. An unmet criterion can name the missing bindings — `qualify()` already returns `missing_bindings`.

**Separation (R1, §3).** "A proposing actor may produce evidence for its own parked proposal. It may not certify that evidence." This is not a count and needs no new doctrine — it is the same separation invariant the repository enforces in three places already: `_grant_refusal:364` (`self_approval_prohibited`), `_apply_modifiers` derived self-approval (entry #15), and `policy.attestation_refusal` (`attestation_self_verified`).

**Authority kind by risk class.** Already generalized into the shared evaluator by Loop 7. `policy.attestation_refusal` requires `HUMAN_CONFIRMATION` when `proposal.risk_class in _HIGH_RISK`, enforces the attestation's risk ceiling, and derives self-verification from identity. Step 3 should **call it, not re-derive it** — re-deriving is how the pattern this program has found seven times begins.

**Staleness (entry #14).** `adapter._is_stale` compares `proposal.state_snapshot` against `_state_version[target_reference]`. Step 1's V1 correction means the parked record retains the whole `Proposal`, so the snapshot is there.

## 4. The evaluator boundary, made concrete

§3: "Resumption is an evaluator operation, not an actor operation. The proposing actor never holds the resumption decision."

That is enforceable structurally, and the two prior steps make it obvious how:

| Input | Who supplies it | Why it matters |
|---|---|---|
| Evidence items | the **actor** — R1 permits this | producing evidence is not certifying it |
| Verifier registry | the **evaluator** | step 2 already made naming a verifier insufficient; holding one is the evaluator's |
| Current state version | the **evaluator** | it lives on the adapter, not on the record — an actor cannot assert the world hasn't moved |
| Parked record | the **registry** | retains the `Proposal` that gets re-evaluated |

Note what this means: **the current state version cannot be read from the parked record**, because the record was written before the delay that makes staleness a risk. It must be supplied at resumption time. That is the mechanical expression of "does not replay a decision made under earlier conditions."

## 5. Seventh instance, recorded

`DELEGATED_POLICY` — a non-human authority kind valid at low and medium risk — exists only in `decision_overwrite.py`. `policy.py` has no concept of it: `attestation_refusal` requires `HUMAN_CONFIRMATION` at high risk but has no rule admitting delegated policy below it, because the kind is unknown to the shared evaluator.

This is adjacent to R4 and is **recorded, not acted on**. Generalizing an authority kind is a doctrine change, not a step-3 implementation detail.

## 6. Blast radius

Larger than the prior two cycles, and the grade reflects it. Step 3 adds `resume` to `PendingVerificationRegistry` — a real state transition on governance state — and a new module for §4's criteria reporting. It still does not modify `policy.py` and does not convert any caller.

The failure mode that matters: a resumption that returns `allow` for a proposal that should still be parked is an authority bypass, not a wrong shape.

## 7. Risk grade

**L3.** Higher than steps 1 and 2. Those described; this transitions. A defect here grants rather than mis-describes.

## 8. Next

`/qor-plan`.
