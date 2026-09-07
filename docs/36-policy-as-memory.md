# Policy as Memory

## Purpose

Policies are memory, but they are high-authority memory. A policy is retained information that directly changes what an agent is allowed to do — which means a stale, spoofed, or wrongly recalled policy does not merely misinform behavior, it *authorizes* the wrong behavior.

This document defines how policies are represented, stored, recalled, certified, updated, and revoked as durable memory objects, and why every one of those verbs is stricter for policy than for ordinary facts, traces, or summaries.

## Why policy memory is not ordinary memory

| Property | Ordinary fact memory | Policy memory |
|---|---|---|
| Wrong recall costs | degraded answer quality | wrong authorization |
| Staleness | reduced usefulness | rules that no longer apply keep applying |
| Conflict | contradiction to resolve | two authorities claiming the same scope |
| Missing | narrower context | undefined governance — fail closed |
| Forgery | false belief | authority laundering |

The memory threat model ([`15-memory-threat-model.md`](15-memory-threat-model.md)) treats policy poisoning as an authority-laundering path, and [`04-governance-and-pama.md`](04-governance-and-pama.md) already classifies policy mutation at the strictest end of the decision table in [`33-pama-decision-table.md`](33-pama-decision-table.md). This document defines the object those protections defend.

## Policy memory type

A policy memory unit is a memory unit (per [`../schemas/memory-unit.schema.json`](../schemas/memory-unit.schema.json)) whose type marks it as policy and which additionally carries:

```text
policy_id
policy_version
issuing_authority
approval_refs
scope                # actors, tenants, memory types, consequence classes governed
effective_from
effective_until      # or none, with review_by required instead
supersedes           # prior policy_version, when applicable
revocation_ref       # populated on revocation
conflict_precedence  # rank or rule reference for conflict resolution
enforcement_points   # boundaries expected to consume this policy
```

Required metadata invariants:

- `issuing_authority` and `approval_refs` must be reconstructable; a policy whose authority cannot be reconstructed is not a policy, it is a claim.
- Every policy is versioned. There is no unversioned policy mutation — an edit is a new `policy_version` with `supersedes` set, per [`27-schema-registry-and-type-evolution.md`](27-schema-registry-and-type-evolution.md) semantics.
- Open-ended effectiveness requires a `review_by` obligation; policies do not get to be simultaneously permanent and unexamined.

## Authority and certification requirements

Policy memory takes the strictest path through every gate this architecture has:

- **Write**: creating or mutating policy is the `policy mutation` row of the PAMA decision table — never below `require_review`, defaulting to `require_external_verification`, with human approval the doctrine expectation for governance-rule changes.
- **Certification**: a policy enters active enforcement only when certified; certification binds the policy version, scope, and approval context. An uncertified policy may exist as a draft memory but must not be consumed by any enforcement point.
- **Estimator firewall**: no estimator output — confidence, usage frequency, predicted utility — may create, modify, activate, or deactivate a policy. Estimators may *flag* policies (stale, conflicting, frequently overridden) as evidence for a governed review.

## Expiration and revocation

```text
expired policy    -> not enforceable; recall returns it only as historical
revoked policy    -> not enforceable; revocation_ref preserved; tombstone per doc 28
superseded policy -> not enforceable; retained as history with supersession link per doc 18
```

Rules:

- Expiry and revocation are lifecycle transitions with receipts, not deletions. Enforcement history must remain auditable: *which* policy version authorized a past action is permanently reconstructable per [`31-recovery-rollback-and-replay.md`](31-recovery-rollback-and-replay.md).
- Revocation propagates with at least the urgency of the policy's blast radius: enforcement points listed in `enforcement_points` must observe revocation before their next consequential decision, or fail closed.
- A revoked policy's derived artifacts (cached decisions, compiled rule sets, context snippets) are deletion-propagation targets per [`28-retention-deletion-and-tombstones.md`](28-retention-deletion-and-tombstones.md).

## Conflict between policies

Policy conflict is a first-class conflict type under [`17-conflict-resolution-engine.md`](17-conflict-resolution-engine.md), with stricter resolution rules:

1. **Overlap detection is mandatory.** Two active policies with intersecting scope and incompatible outcomes are a governance incident, not a soft inconsistency.
2. **Precedence is declared, not inferred.** Resolution uses `conflict_precedence` and issuing authority — never recency alone, never estimator confidence, never whichever policy was recalled first.
3. **Unresolved conflict fails closed** for the contested scope: the strictest applicable outcome governs until a governed resolution lands.
4. The resolution itself is a policy mutation, with the full authority path that implies.

## Recall rules during context assembly

Policy recall goes through the governed recall planner ([`26-governed-recall-planner.md`](26-governed-recall-planner.md)) with policy-specific admission rules:

- **Completeness over relevance.** For a governed action, the planner must admit the *applicable policy set* — every active, in-scope policy — not the top-k semantically relevant ones. A missing applicable policy is a recall failure even if nothing false was recalled.
- **Version pinning.** Assembled context records which `policy_version` was admitted; the decision receipt binds to it.
- **No stale admission.** Expired, revoked, and superseded policies are admitted only with explicit historical marking, and never into an enforcement path.
- **Scope filtering still applies.** A policy from another tenant is not an applicable policy, however relevant it looks — the cross-tenant relevance trap applies to policies with higher stakes than to facts.
- **Uncertain applicability escalates.** If the planner cannot determine whether a policy's scope covers the current action, the conservative reading applies pending review; uncertainty does not default to "not applicable."

## Conformance fixture recommendations

| Case | Expectation |
|---|---|
| Stale policy retention | expired policy is not enforced; recall marks it historical; enforcement point that would have used it fails closed or escalates |
| Policy version drift | action authorized under `p-N` is not re-justified by `p-N+1`; receipts distinguish versions — see [`../fixtures/policy-estimator-version-drift.json`](../fixtures/policy-estimator-version-drift.json) |
| Conflicting active policies | strictest-applicable governs; conflict surfaces as incident; no recency-wins |
| Estimator proposes policy change | proposal enters review; no estimator-authored activation — the example 8 pattern of `33-pama-decision-table.md` |
| Policy spoofing | policy-typed memory without reconstructable `issuing_authority` and certification is rejected at every enforcement point — see [`../fixtures/authority-laundering.json`](../fixtures/authority-laundering.json) |
| Incomplete policy recall | context assembly missing an applicable active policy is a failed fixture even when everything admitted was correct |

A dedicated `stale-policy-retention` fixture should join the fixture set alongside the fixture-versioning work tracked in issue #43.

## Doctrine

A policy is memory about what is allowed.

That makes it the one class of memory the system must never learn, infer, or optimize into existence. Policies are written under authority, recalled completely, enforced by version, and retired by receipt — and every estimator in the system is merely a witness to that process, never a party to it.
