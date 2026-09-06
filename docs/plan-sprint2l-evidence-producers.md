# Plan: Sprint 2l — migrating the evidence producers

**change_class**: feature
**Risk Grade**: L3
**Session**: 2026-09-05T0540-4fc4e9
**Research**: `docs/research-brief-sprint2l-evidence-producers-2026-09-05.md`
**Iteration**: 3 (audit attempt 3: PASS; grounds V1-V3 discharged)
**Implements**: ADR-037 **step 4b-1** — migrate what can produce evidence, additively

## Objective

Give the three modules that already hold checkable material the ability to produce real `EvidenceItem`s and discharge through R5's ladder. Nothing flips; nothing existing changes behaviour.

## Why this is a separate cycle, stated honestly

4a split step 4 because the discharge path did not exist — a doctrinal halt. **This split has a weaker justification and is recorded as such.** There is no halt: converting three modules and flipping together would strand nobody. The reasons are risk and reviewability.

- The flip breaks **57 tests across 18 files**. A mistake in any one converted module would be masked by the other 54 failures.
- Four modules must be *decided about* rather than converted, and that is the operator's call.

## Boundaries

**In scope**: `procedural_memory`, `reusable_grants`, `dashclaw_external_verdict` gain evidence production and a qualified-discharge path, plus tests.

**Explicitly out of scope:**

| Not built | Why |
|---|---|
| The flip | 4b-2. `_apply_review` untouched; every existing caller keeps working |
| The four digest-less modules | They hold a name and nothing checkable. Converting them would mean **inventing** an `artifact_ref` and `digest` to satisfy the classifier — the caller-asserted defect dressed as a migration. ADR-037 rules they park; whether that is acceptable is raised, not assumed |
| Scaffolding-test re-homing | 4b-2, since those tests only break at the flip |

## Design decisions

**LD1 — Evidence is built from material the module already holds, never minted for the classifier.**
This is the cycle's whole claim and the pattern every later conversion will copy. `procedural_memory` has `content_sha256` and `skill_version_ref`; `reusable_grants` has `grant_body_digest`; `dashclaw_external_verdict` has provider execution evidence and commit bindings. Each `EvidenceItem` is assembled from those. **No module gains a new digest field to make itself classifiable** — if the material is not already there, the site is 4b-2's problem, not this cycle's.

**LD2 — `procedural_memory` targets `verified`, not the `asserted` its risk class would permit.**
R5 accepts `asserted` at low and medium. `procedural_memory` can do better: the algorithm that re-hashes the payload and compares to `content_sha256` already exists at `:143`, and LD5 now lets the module **export it** for the evaluator to register. Settling for `asserted` because the risk class permits it would be taking the weakest reading of the ladder in the one place the strongest is available.

**LD3 — Each module exposes evidence production; none exposes discharge.**
`evidence_for(...) -> tuple[EvidenceItem, ...]` and nothing more. The module produces; the caller decides whether to route through `evaluate_with_qualified_evidence`. R1 is the reason: producing evidence and certifying it are different acts, and a module that both produced and discharged its own evidence would be doing both.

**LD4 — `dashclaw_external_verdict` is the adversarial case, and separation is shown by lineage, not by a label (audit V3).**

The provider produces the verdict; the module must not certify it. This is R1's separation with a real second party rather than a fixture.

Iteration 2 said provider-produced evidence must be "distinguishable from module-produced" without saying how — and **`EvidenceItem` carries no producer field of any kind**. That is deliberate: Loop 10's audit declined exactly this, calling it the eighth instance of the caller-asserted pattern, and `test_evidence_item_gains_no_principal_field` now asserts the absence of `verifier_principal_id`, `principal`, `actor_id` and `produced_by`. An implementer taking the old wording at face value would have added `produced_by`, satisfied the DoD, broken Loop 10's test, and put a control's input back in the hands of the party it constrains — in the cycle whose LD1 exists to prevent exactly that.

**R2's lineage machinery already answers R1's question.** Provider and module evidence differ in artifact root and failure domain, so they land in different dependence groups:

    provider: artifact_ref="dashclaw://verdict", failure_domain="dashclaw-provider"
    module:   artifact_ref="agentmem://skill",   failure_domain="agent-memory-local"
    group_by_dependence -> 2 independent groups

This is the stronger property, not merely the available one. A `produced_by` string asserts an origin; distinct dependence groups are a **derived** statement that the two cannot fail together — which is what R1 means when it says the proposer may produce but not certify.

**LD5 — A module may supply a verifier *implementation*; it may never hold the *registry* (audit V1).**

Iteration 1 said modules "name verifiers; they do not supply them", which conflicted with LD2: if a module may only name one, nothing ever runs the re-hash, every item stays `asserted`, and LD2's claim that `procedural_memory` reaches `verified` was aspirational — passing only via a test that supplied the verifier itself.

The two things LD5 had conflated:

| | Whose | Why |
|---|---|---|
| **Holding the registry** — deciding which verifiers are trusted | the **evaluator's**, always | registering your own verifier is certifying your own evidence |
| **Supplying an implementation** — exporting a callable | the **module** may | offering a mechanism is not exercising authority over it |

A module exporting `verify_*(item) -> bool` has certified nothing: the evaluator still decides whether to register it, and an unregistered verifier leaves the item `asserted`. This is Loop 6's `RatificationRegistry` shape — the module supplies the mechanism, the evaluator holds the authority to use it.

`procedural_memory` already contains the algorithm at `:143` (`if artifact.content_sha256 != expected_digest`). It needs an export, not a new capability.

**LD6 — Legacy and qualified paths are asserted side by side, in the same test.**
For each module, one test asserts its evidence discharges through the ladder and another asserts its existing `review_satisfied` path still works. Both, in the same suite, because "additive" is a claim that can be checked and should be.

**LD7 — No module stops setting `review_satisfied`.**
That removal belongs to the flip. Doing it here would break callers with no gate change to justify it, and would make this cycle's blast radius indistinguishable from 4b-2's.

## Affected files

| File | Change |
|---|---|
| `reference/agentmem_ref/procedural_memory.py` | **modified** — `evidence_for` from `content_sha256` / `skill_version_ref` |
| `reference/agentmem_ref/reusable_grants.py` | **modified** — `evidence_for` from `grant_body_digest` |
| `reference/agentmem_ref/dashclaw_external_verdict.py` | **modified** — `evidence_for` from provider execution evidence |
| `reference/tests/test_evidence_producers.py` | **new** |

`policy.py` unmodified. `evidence_qualification.py` unmodified.

## Feature Inventory Touches

| ID | Feature | Disposition |
|---|---|---|
| FX016 | Modules holding checkable material produce real `EvidenceItem`s that discharge through R5's ladder | NEW |

## Definition of Done

1. `procedural_memory.evidence_for` returns an `artifact_bound` item built from `content_sha256` and `skill_version_ref` — asserted by classifying it with `qualify()` and reading `artifact_bound`.
2. **That item reaches `verified`** under a registry whose verifier re-hashes the payload (LD2), and **`refuted` when the payload does not match its digest** — the verifier must be real, not a `lambda: True`.
3. `reusable_grants.evidence_for` returns an `artifact_bound` item built from `grant_body_digest`, and it is `refuted` when the grant body is tampered with — reusing Loop 6's tamper detection rather than a new one.
4. `dashclaw_external_verdict.evidence_for` returns items built from provider execution evidence, and **provider-produced and module-produced evidence land in different dependence groups** (LD4, audit V3) — asserted through `group_by_dependence`, never through a producer label.
4b. **`EvidenceItem` gains no producer field** (audit V3): asserted over its dataclass fields, extending Loop 10's absence test rather than replacing it, so the tenth instance cannot be introduced to satisfy DoD 4.
5. **Each module is exercised at the risk classes it actually constructs** (audit V2), not at whichever class passes most easily:
   - `procedural_memory` constructs **both** `low` and `high`. At low, its evidence discharges with `discharge_authority == delegated_policy`. **At high, the full R5 requirement is asserted** — `verified` binding **and** a `human_confirmation` attestation — because that is the path where discharge is hardest and where 4b-2 would otherwise discover a failure this cycle had reported as proven.
   - `reusable_grants` and `dashclaw_external_verdict` construct no `risk_class` literal; it arrives from the caller. Their tests choose **high**, deliberately, since a grant and an external verdict are the cases where the weaker reading would be least defensible.
5b. A module whose evidence is only `asserted` **does not** discharge at high risk, asserted per module — the negative half of DoD 5, so passing cannot come from the ladder being lenient.
6. **No module ships a verifier registry** (LD5), asserted over each module's public surface — while `procedural_memory` and `reusable_grants` **do** export verifier callables, asserted as present and as returning `False` on tampered input.
7. **No module exposes a discharge method** (LD3) — `evidence_for` and nothing that returns a `Decision`.
8. **No module gains a new digest field** (LD1): asserted by diff — the digests used already existed before this cycle.
9. **Every module's legacy `review_satisfied` path still works**, asserted per module alongside the qualified path (LD6).
10. `review_satisfied` is still set by each module (LD7), asserted by diff.
11. All 1050 prior tests pass, unchanged. `policy.py` unmodified by diff.
12. Validators clean; no schema modified.

## CI Commands

```
python -m unittest discover -s reference/tests -t reference
python scripts/validate_schemas.py
python scripts/validate_fixtures.py fixtures
```

## Rollback

Revert the three modules; delete the new test file. Nothing else changes.

## Next

`/qor-implement`. Audit attempt 3 returned PASS with no further conditions.

Attempts 1 and 2 vetoed on V1-V3: LD2 and LD5 could not both hold, leaving the verifier LD2 depended on with no home (V1); DoD 5 exercised only the low-risk half of a module that demonstrably operates at high risk (V2); and DoD 4 asked for a producer distinction `EvidenceItem` deliberately cannot express, whose easy fix would have reintroduced the field Loop 10 declined (V3). All three are discharged.
