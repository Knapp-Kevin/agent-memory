# Research Brief: Sprint 2c — deletion authority, and the SEC-04 trust anchor

**Date**: 2026-09-04
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 4.
**Investigated**: GAP-SEC-03 and GAP-SEC-04.
**Implementable this cycle**: GAP-SEC-03 only. GAP-SEC-04 terminates in an owner decision (§4).

## 1. GAP-SEC-03 — five verified defects in `governed_delete`

All re-derived against post-Loop-2 code (`probe_sec03.py`).

**The guard exists and works on the write path.** A commit with `state_snapshot="v99"` against actual `v1` is correctly refused (`committed: False`). So staleness enforcement is present and functioning — it is simply not applied to deletion.

| # | Defect | Probe result |
|---|---|---|
| D1 | `governed_delete` passes `blocked_by_stale=False` unconditionally (`adapter.py:600`) | delete with `state_snapshot="v99"` against actual `v1` → **committed** |
| D2 | `fact_uuid` is never checked against `proposal.target_reference` | delete claiming `target_reference="mem:UNRELATED"` while passing `mem:A`'s fact uuid → **committed**, victim tombstoned |
| D3 | The resulting tombstone is **falsified** | tombstone records `memory_id: mem:UNRELATED` for a fact belonging to `mem:A` |
| D4 | No tenant check before `self._substrate.delete_fact(fact_uuid)` | tenant B `permanent_deletion` of tenant A's fact → **committed**, fact physically gone |
| D5 | No existence check | deleting `"does-not-exist"` → **committed**, tombstone written |

**D3 deserves separate weight.** D2 is an authorization bypass; D3 is *evidence corruption*. The tombstone is the record that survives the deletion, and it can be made to attest that a fact belonged to a memory it never belonged to. A later reader of the governance record is misled, not merely under-protected.

**D4 is not addressed by Loop 2.** Loop 2 fixed identifier *minting* so two adapters cannot collide. `governed_delete` takes a `fact_uuid` directly and never checks ownership, so cross-tenant physical deletion remains fully open. Confirmed by probe against current code.

`_is_stale` (`adapter.py:273-278`) returns `False` when `state_snapshot` is empty — the field defaults to `""`, so the guard is opt-in even where it is wired. 17 `governed_delete` call sites exist.

## 2. GAP-SEC-04 — the artifacts are already content-addressed, and the check is never run

This is a materially different picture from "verify by schema only".

**The integrity mechanism already exists.** `ratify_reusable_grant` (`reusable_grants.py:243-259`) builds the grant id as a digest of the body:

```python
body = {"proposal_id": ..., "operation": ..., "scope_refs": ..., "issued_at": ...,
        "expires_at": ..., "revocation_mechanism_ref": ..., "evidence_refs": ...}
grant = {"grant_id": f"reusable-grant:{_digest(body)}", **body, ...}
```

`_digest` is `sha256(rfc8785.dumps(value))` — canonical JSON, so the grant is self-authenticating by construction. Verified: an untampered grant's body reproduces its stated `grant_id` exactly.

**`evaluate_reusable_grant` never recomputes it.** Confirmed by source inspection: it calls `receipts.validate` for the schema and contains no `_digest` call. Probe:

| Case | `grant_id` still matches body | Evaluated status |
|---|---|---|
| untampered | **True** | `current` |
| `expires_at` → 2030, id untouched | **False** | **`current`** |
| `scope_refs` widened, id untouched | False | `not_applicable` / `scope_mismatch` |
| `expires_at` → 2030 **and id recomputed** | True | **`current`** |

**Counter-evidence to the deep audit, recorded honestly.** The audit reported that editing `scope_refs` "also evaluated `current`". Against the harness projection it does **not** — the projection cross-check catches it. The audit's result required also supplying a matching caller-built projection. Row 3 is a genuine partial refutation of that sub-claim; the `expires_at` case (row 2) stands exactly as reported.

**`verify_approval_evidence` has zero production callers.** Verified by grep: seven references, all in `test_approval_evidence.py`. The verification routine exists, is tested, and is invoked by nothing in the runtime.

## 3. Why the obvious SEC-04 fix does not work

Row 4 is the finding that matters. Recomputing the digest and comparing it to `grant_id` **does not close GAP-SEC-04**, because `_digest` is unkeyed: anyone who can edit the body can recompute the id. The probe demonstrates it — tamper the expiry, recompute the id, and evaluation returns `current` with a body that is perfectly self-consistent.

Self-certification is not verification. The transcript invariants the deep audit graded these gaps against say it directly: *memory cannot self-authorize*, and *the executor is not the certifier*. A grant that vouches for itself is exactly the shape those invariants forbid, and a digest check would make the artifact *look* verified while leaving the actual threat model — a caller-supplied artifact — untouched.

Shipping the digest check alone would be a half-measure that reads like a fix. It is worth adding as a corruption detector, but it must not be described as closing SEC-04.

## 4. Owner decision required — the trust anchor

Real closure needs the grant bound to something the caller cannot forge. The options are genuinely different commitments, and this is not a decision to make inside an implementation cycle:

- **(a) Adapter-held issuance registry.** The adapter retains `grant_id`s it issued and refuses any grant it did not issue. Simple, no crypto, no key management — but it is per-process state that does not survive restart or cross a process boundary, so a reusable grant stops being portable, which is its point.
- **(b) Keyed digest (HMAC).** `cryptography` is already a declared dependency. Portable and stateless to verify, but introduces a key: who holds it, how it rotates, and what happens on compromise.
- **(c) Bind to independently-held ratification evidence.** `verify_approval_evidence` already exists and is uncalled (§2). Wiring evaluation to require verified ratification evidence, rather than the caller's copy of the grant, matches the doctrine most closely — the certifier is the ratifier, not the artifact.
- **(d) Declare the host the trust boundary for grants**, as you already did for recall principals. Consistent with the SEC-02 decision, closes the gap by contract rather than by code, and would make the digest check the appropriate and sufficient local control.

(c) and (d) are the two that fit the existing doctrine; (d) is consistent with the decision already taken for recall. This brief does not choose.

## 5. Scope recommendation

**Loop 4 implements GAP-SEC-03 only.** Its five defects have complete, self-contained fixes with no unresolved design question: honour staleness on delete, verify the fact belongs to the claimed target, verify tenant ownership, verify existence, and stop writing falsified tombstones.

**GAP-SEC-04 does not enter an implementation cycle until §4 is answered.** Implementing the digest check now would produce a change that passes every test, closes nothing against the actual threat, and makes the gap look addressed in the ledger. That is the specific failure this program's audit tribunal exists to prevent, and it should not be smuggled past it by an implementer's convenience.

## 6. Risk grade

**L3.** Deletion authority on a shared substrate, with a demonstrated cross-tenant physical delete and a demonstrated falsified governance record. The change makes previously-permitted operations raise, so the 901-test suite and the 17 `governed_delete` call sites are the blast surface.

## 7. Next

`/qor-plan`, scoped to GAP-SEC-03. GAP-SEC-04's §4 decision goes to the operator in the Review Boundary packet.
