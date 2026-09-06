# Plan: Sprint 2e — the ratification trust anchor

**change_class**: feature
**Risk Grade**: L3
**Session**: 2026-09-04T1713-79ea9b
**Research**: `docs/research-brief-sprint2e-ratification-anchor-2026-09-04.md`
**Iteration**: 2 (amended for audit attempt 1 grounds V1-V3)
**Gap**: GAP-SEC-04 (grant path closed)
**Implements**: operator decision of 2026-09-04 — option C code path, option D declarable profile

## Objective

Replace the caller-asserted `ratification_evidence_present` boolean with verification against a ratification record the presenter cannot write, so a tampered grant is detected **even when its content-addressed id has been recomputed to match**.

## Boundaries

**In scope**: `reference/agentmem_ref/reusable_grants.py`, new tests.

**Non-goals**: GAP-ARCH-04's `review_satisfied` and external-verification legs (Loop 7); any schema change; `decision_overwrite`'s bypass of the grant bridge.

## Design decisions

**LD1 — `RatificationRegistry`: registration is a consequence of ratification, not a public method (audit V1).**

The registry exposes `resolve(grant_id)` and **no public way to register an arbitrary grant**. The record is written only from inside `ratify_reusable_grant`, which gains an optional `registry` parameter and registers as part of the ratification act.

Iteration 1 gave it a public `register(grant)` and defended it as an anchor because it refuses to overwrite. **That is the wrong property.** The attacker never needs to overwrite: tamper `expires_at`, recompute `grant_id`, and that is a *new* id with nothing to replace. `register(tampered)` would succeed, all three checks would pass against the attacker's own record, and evaluation would report `current` with `ratification_evidence_verified` — a control that certifies the exact forgery the operator's decision exists to defeat.

The anchoring property is that **an attacker cannot register a tampered grant without performing a valid ratification of it**. `ratify_reusable_grant` raises on self-ratification, on scope or material-condition mismatch against the proposal, on a policy-version mismatch, and on an expiry beyond the proposed validity (`reusable_grants.py:225-241`). A ratification that would produce the tampered values does not pass those preconditions.

Generalizes `decision_overwrite.DurableDecisionRegistry:99-118`, whose docstring already states the authority-boundary intent.

**Declared boundary condition.** In a single-process reference implementation the separation is by ownership, not enforcement: the host constructs the registry and passes it to ratification and to evaluation. A caller handed the registry instance could still reach `_record`. This is stated in the class docstring in the same terms `DurableDecisionRegistry` uses — it demonstrates the authority boundary, it is not a production evidence service — so the limit is disclosed rather than implied.

**LD2 — Verification compares held values, not merely the presence of a record.**
When a registry is supplied, `evaluate_reusable_grant` performs three checks in order:

1. **Integrity** — recompute the body digest and compare to `grant_id`. Mismatch → `invalid` / `grant_body_tampered`.
2. **Registration** — resolve `grant_id`. Absent → `invalid` / `ratification_evidence_unregistered`.
3. **Divergence** — compare the presented grant's authority-bearing fields against the **held record's**: `operation`, `scope_refs`, `issued_at`, `expires_at`, `policy_version_ref`, `ratifying_principal_ref`. Any mismatch → `invalid` / `grant_diverges_from_ratification`.

**The discriminating control is check 2 combined with LD1's registration gate, not check 3 (audit V2, V3).**

Because `grant_id` is a digest of the grant's own body, checks 1 and 2 passing together imply the held and presented bodies are byte-identical under canonical JSON — so **check 3 cannot fail against a tampered grant**. Iteration 1 called it "the one that matters"; it is in fact unreachable for that purpose, and DoD 3 asserted an outcome the design could not produce.

Check 3 is **retained as a consistency assertion**, not as the attack control: it would fire only if ratification and registration ever disagreed, which is a bug rather than an attack, and it costs nothing to keep. It is no longer claimed as the discriminating check and no DoD item tests it as one.

What actually defeats the recompute attack is that the recomputed `grant_id` was never registered, because registering it would have required a valid ratification of the tampered values — which `ratify_reusable_grant`'s preconditions refuse. The attack fails at **check 2**, with `ratification_evidence_unregistered`.

**LD3 — Provenance rides the existing `reasons` vocabulary.**
`ratification_evidence_verified` on the registry path, `ratification_evidence_asserted` on the boolean path.

`reusable-grant-evaluation.schema.json` is `additionalProperties: False` and is validated by `evaluate_pama_with_reusable_grant`, so an `evidence_source` field would require a public schema change — Sprint 4's boundary freeze, not this cycle. `reasons` already carries machine-readable tokens of exactly this kind. Verified safe: nothing asserts `reasons == []` on success.

Both paths are annotated. Silence must not mean "verified" — absence of a marker cannot be allowed to imply the stronger claim.

**LD4 — `ratification_evidence_present` is retained as the declared option-D profile.**
Registry absent and boolean `True` → `current` with `ratification_evidence_asserted`. This *is* option D: a deployment declaring the host its trust boundary. It stays available and stays labelled, so a reader of the evaluation can always tell which posture produced it.

Registry absent and boolean `False` → `invalid` / `ratification_evidence_missing`, unchanged.

**LD5 — Do not touch the external-verification refusal.**
`evaluate_pama_with_reusable_grant:397` already refuses to discharge anything but `REQUIRE_REVIEW`. Research F4 established that the grant path is therefore not implicated in GAP-ARCH-04's external-verification leg at all; the two `decision_overwrite` sites bypass this bridge by building their `Proposal` directly. That is Loop 7's work and must not be smuggled in here.

## Affected files

| File | Change |
|---|---|
| `reference/agentmem_ref/reusable_grants.py` | `RatificationRegistry` (LD1); optional `registry` and three-check verification in `evaluate_reusable_grant` (LD2); provenance reasons (LD3) |
| `reference/tests/test_ratification_anchor.py` | **new** — the recompute attack, each check in isolation, both profiles, schema validity |

## Feature Inventory Touches

| ID | Feature | Disposition |
|---|---|---|
| FX010 | Reusable grant evaluation verifies against an independently-held ratification record | NEW |

## Definition of Done

1. Untampered grant with a registry → `current`, `reasons` contains `ratification_evidence_verified`.
2. `expires_at` tampered, `grant_id` untouched, registry supplied → `invalid` / `grant_body_tampered`.
3. **`expires_at` tampered AND `grant_id` recomputed to match, registry supplied → `invalid` / `ratification_evidence_unregistered`.** The exact case that defeated the digest-only fix in Loop 4's probe. It fails at check 2 because the recomputed id was never ratified (audit V2).
3b. **The registration gate is the control, and is tested as such**: attempting to obtain a registration for the tampered grant by ratifying it must raise, because `ratify_reusable_grant`'s preconditions refuse an expiry beyond the proposed validity. An implementation that exposed a public `register(grant)` would pass DoD 3 and fail this.
3c. `RatificationRegistry` exposes no public method that registers an arbitrary grant dict — asserted over its public surface, so the V1 defect cannot reappear by later convenience.
4. A grant never registered, registry supplied → `invalid` / `ratification_evidence_unregistered`.
5. Registry absent, boolean `True` → `current` with `ratification_evidence_asserted` (option D profile, labelled).
6. Registry absent, boolean `False` → `invalid` / `ratification_evidence_missing`, unchanged.
7. Registration refuses to overwrite an existing `grant_id`. Retained as a defence, but explicitly **not** the anchoring property (audit V1) — DoD 3b tests the property that is.
8. Every evaluation result still validates against `reusable-grant-evaluation.schema.json`; no schema file is modified.
9. `evaluate_pama_with_reusable_grant` still refuses to discharge `require_external_verification`, asserted directly so LD5's restraint is verified rather than assumed.
10. **All 925 prior tests pass.** The two existing callers pass no registry and must be unaffected.
11. `validate_schemas.py` and `validate_fixtures.py fixtures` clean.
12. The seal records GAP-SEC-04 as closed **for the grant path**, and records that ARCH-04's external-verification leg is relocated to Loop 7 rather than closed.

## CI Commands

```
python -m unittest discover -s reference/tests -t reference
python scripts/validate_schemas.py
python scripts/validate_fixtures.py fixtures
```

## CI Coverage Exemptions

`reusable-grant-authority-transition` and the doctrine-evidence workflows are triggered. DoD 10 covers them: the full suite they invoke must pass.

## Rollback

`git checkout -- reference/agentmem_ref/reusable_grants.py` and delete the new test file.

## Next

`/qor-audit`. L3: adversarial mode; independent verification that check 3 is not redundant with check 1, and that the option-D path cannot be reached silently.
