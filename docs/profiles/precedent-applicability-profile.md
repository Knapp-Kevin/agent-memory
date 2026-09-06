# Deterministic Precedent Applicability Profile

Status: reference V0.1 implementation profile for issue #181.

## Purpose

This profile consumes the existing Governance Context Projection and determines whether prior governed decision episodes are materially applicable context to a current action.

It does not create permission.

```text
decision history
!= reusable authority

resolved one-time approval
!= standing grant

similarity / repetition
!= permission
```

The V0.1 consumer is intentionally deterministic. It accepts only `exact_identity` and `deterministic_condition_match` derivation modes. Semantic similarity, embeddings, LLM judges, learned matchers, and hybrid estimators are rejected in this slice.

## Input

Canonical input remains the existing:

`schemas/governance-context-projection.schema.json`

The consumer uses already-projected dimensions such as:

- scope relationship;
- supportive, cautionary, contradictory, and neutral precedent;
- material-condition comparison states;
- precedent validity;
- human, policy, runtime, inference, and external-evidence provenance;
- independent-human adjudication marking;
- outcome and policy-version references.

No parallel decision-memory object is introduced.

## Output

Schema:

`schemas/precedent-applicability-result.schema.json`

Reference consumer:

`reference/agentmem_ref/precedent_applicability.py`

The result reports separately:

```text
applicability
supporting_precedent_refs
cautionary_precedent_refs
material_matches
material_differences
unknown_conditions
stale_or_invalid_reasons
independent_human_evidence_count
policy_or_derived_evidence_count
incident_or_negative_evidence_present
recommended_handling
authority_effect
can_authorize_execution
```

`authority_effect` is fixed to `none` and `can_authorize_execution` is fixed to `false`.

Recommended handling is advisory context only:

```text
reduce_redundant_review
normal_review
escalate
block_proposal_not_authority
```

No handling label becomes a permitted action or execution token.

## Conservative V0.1 rules

Review reduction is proposed only when:

1. scope relationship is exactly `same`;
2. at least one current supportive precedent is an exact/material match;
3. no material condition is unknown;
4. no material difference is present;
5. no current materially relevant cautionary/contradictory precedent is present.

Other cases remain visible and conservative:

```text
scope mismatch/crossing -> materially_different + escalate
material condition mismatch -> materially_different + normal_review
unknown condition -> insufficient_evidence + normal_review
current relevant negative precedent -> conflicting + escalate
matching but expired/revoked/stale precedent -> stale + normal_review
no materially comparable precedent -> insufficient_evidence + normal_review
```

A future profile may make finer distinctions, but it may not infer standing authority from repetition.

## Evidence attribution

Independent human evidence is counted only when the projection provenance is:

```text
source_type = human_adjudication
independent_adjudication = true
```

Policy outcomes, runtime observations, memory inference, and external evidence remain separately counted as derived/non-independent evidence.

A policy-generated allow therefore cannot recursively inflate the independent-human evidence count.

Relevant negative evidence is counted and surfaced even when positive approvals are more numerous. Frequency is not a majority vote over incident evidence.

## Required adversarial scenarios

Fixture:

`fixtures/precedent-applicability-matrix.json`

Executable tests:

`reference/tests/test_precedent_applicability.py`

The bounded V0.1 set covers:

1. repeated safe equivalent feature-branch pushes;
2. force push to a protected branch;
3. stale/failed CI or changed state;
4. cross-tenant near-match;
5. one relevant incident among many prior approvals;
6. one human approval followed by many policy-generated allows;
7. expired approval evidence;
8. novel/insufficient evidence with an unknown material condition.

## Metrics

The metrics are deliberately separate rather than collapsed into one score:

`reports/examples/precedent-applicability-results.example.json`

The required fixture currently expects:

```text
cases evaluated:                                      8
redundant-review reductions proposed:                 2
unsafe-equivalence false positives:                   0
material-difference misses:                           0
negative-precedent misses:                            0
cross-scope leakage failures:                         0
stale-precedent reuse failures:                       0
independent-human/derived attribution errors:         0
novel-case escalation rate:                         1.0
```

Zero unsafe-equivalence false positives on this bounded fixture is completion evidence for these scenarios only. It is not a universal safety claim.

## What V0.1 proves

Within the specified deterministic scenarios, the implementation demonstrates that:

- material differences remain explicit;
- prior safe actions do not generalize to force/protected-branch actions;
- scope mismatch cannot lower review friction;
- expired/stale precedent remains historical rather than current authority;
- negative precedent survives positive frequency;
- policy-derived outcomes do not become independent human approvals;
- unknown conditions remain unknown;
- advisory applicability cannot authorize execution.

## What V0.1 does not prove

V0.1 does not provide:

- standing grants;
- automatic policy mutation;
- semantic/probabilistic precedent retrieval;
- cross-organization precedent reuse;
- human-factor evidence that the proposed reductions improve operator behavior;
- a universal false-positive guarantee;
- final PAMA or external-governor decisions.

Those remain separate follow-on work with their own authority and evidence gates.
