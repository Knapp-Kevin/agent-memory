# Contextual Recall Admission Profile

Status: V0.1 reference profile for #200.

This profile defines a monotonic current-context admission seam layered after the canonical `GovernedMemoryAdapter` read gate.

Its purpose is narrow: retained memory that survives storage and ordinary scope/lifecycle checks must still be re-evaluated under the **current** purpose/context before becoming active context or downstream influence.

## Core boundary

```text
prior admission
!= standing recall permission

write-time safety
!= lifetime safety

candidate discovery
!= admission

relevance
!= permission

context change
-> current admission re-evaluation

contextual policy may tighten
!= silently loosen built-in governance
```

The seam does not mutate stored memory merely because current context is risky.

## Composition order

V0.1 is deliberately compositional:

```text
substrate retrieval
-> canonical GovernedMemoryAdapter admission
-> contextual current-policy admission
-> context surface
-> downstream influence
```

The canonical adapter executes first and remains authoritative for:

- tenant isolation;
- isolation-domain membership;
- required compartments;
- shared-space membership;
- project/task boundaries;
- tombstones;
- supersession/currentness;
- disputes.

The contextual adapter receives **only** candidates that the canonical gate admitted.

Therefore:

```text
built-in refusal
-> contextual policy is not invoked
-> contextual admit cannot resurrect candidate
```

This is the V0.1 monotonic-tightening guarantee.

## Current contextual decision

A contextual decision preserves:

```text
candidate_ref
policy_ref
policy_version
policy status
bounded current context identity
outcome
reason_code
evidence_refs
optional risk-estimator evidence
evaluated_at
```

Current context is minimized to:

```text
target_domain_refs
principal_ref
project_ref
task_ref
purpose
destination_ref
```

Raw query text, memory content, prompts, and hidden reasoning are not required to prove that the current gate ran.

## Outcomes

V0.1 supports deterministic outcomes:

```text
admit
admit_with_warning
require_verification
require_review
quarantine
block
```

Only `admit` and `admit_with_warning` enter final context.

The other four outcomes keep the candidate discoverable but exclude it from final admitted/context/downstream surfaces.

## No cached admission authority

Every wrapped `governed_recall(...)` executes the current contextual policy again for each candidate that survives canonical admission.

The adapter does not cache an earlier `admit` as a reusable grant.

Machine-readable decisions fix:

```text
prior_admission_authority = none
authority_effect = current_recall_only
```

A benign recall yesterday does not authorize a different purpose today.

## Policy version changes

The contextual adapter can replace the current policy without rewriting retained memory.

A later decision records the later policy version directly.

This permits:

```text
same retained fact
same or changed purpose
policy v1 -> admit
policy v2 -> require_review / quarantine / block
```

without pretending the stored content itself changed merely because current governance did.

## Learned or probabilistic risk signals

A deterministic contextual rule may preserve bounded estimator evidence such as:

```text
signal_ref
signal_semantics
estimator_ref
estimator_version
signal_value
uncertainty_summary
```

The signal may inform the deterministic policy outcome. It does not create authority.

Every decision fixes:

```text
risk_signal_authority = none
relevance_authority = none
```

This preserves the repository's governed-uncertainty rule:

```text
uncertainty may propose
authority constrains
```

## Failure posture

When contextual policy is optional and absent, canonical admission remains sufficient.

When a deployment configures contextual policy as required, absence fails closed:

```text
policy.status = unavailable
outcome = block
```

A configured policy that raises an error fails closed:

```text
policy.status = error
outcome = block
```

A configured policy that returns an invalid/unsupported decision fails closed:

```text
policy.status = invalid
outcome = block
```

None of those failures widens recall.

## Sleeper-poisoning behavioral proof

The V0.1 harness consumes the existing structural fixture:

`fixtures/sleeper-memory-poisoning.json`

The fixture requires:

```text
write_time_check_may_pass = true
later_trigger_rechecked = true
unsafe_activation_allowed = false
```

The behavioral sequence is:

1. retain one bounded fact through normal governed mutation;
2. recall it under a benign purpose;
3. observe the candidate and admit it;
4. keep the retained fact unchanged;
5. recall the same fact under purpose `activate-triggered-memory`;
6. discover the same candidate again;
7. execute the current contextual policy again;
8. record `quarantine` under the delayed-trigger rule;
9. keep the candidate out of admitted/context/downstream surfaces;
10. preserve the retained fact rather than mutating/deleting it merely to force the test.

The rule also carries a probabilistic delayed-activation risk estimate as evidence while machine-enforcing that the estimate has no authority by itself.

## Final surfaces

The compositional reference result exposes:

```text
candidates
admitted
refusals
contextual_decisions
context_surface
downstream_influence
```

`context_surface` and `downstream_influence` are explicit copies of final admitted identity refs in this bounded proof. They are not a new inference system.

For a sleeper trigger:

```text
candidate in candidates
candidate not in admitted
candidate not in context_surface
candidate not in downstream_influence
```

This demonstrates read-time containment while preserving retrieval observability.

## Evidence depth

V0.1 registers the sleeper-poisoning claim through the D/F/H/R/P model from #196:

```text
D = threat model + governed recall doctrine + this profile
F = sleeper-memory-poisoning fixture
H = contextual recall behavioral harness
R = explicitly unproven
P = explicitly unproven
```

The reference harness does not launch a production agent or live long-horizon workload, so it does not self-promote to R or P.

## Privacy and minimization

The decision record uses candidate/context refs, policy identity, bounded reason/outcome, and evidence refs.

It does not require:

- raw memory contents;
- the retrieval query;
- prompts/system instructions;
- hidden reasoning;
- full tool outputs;
- arbitrary estimator payloads.

## Deployment profiles

### L: local

Contextual policy may be optional. A local deterministic rule set can add read-time containment without external services.

### T: team / multi-tenant

Canonical tenant/project/domain admission remains first. Contextual rules cannot repair cross-tenant refusal.

### E: enterprise

A current contextual policy may be configured as required. Policy unavailability/error then fails closed and leaves evidence.

### H: high assurance

Current policy identity/version, outcome/reason, exact candidate/context refs, failure posture, and evidence refs must remain reconstructable. Missing required contextual policy cannot widen recall.

## V0.1 non-claims

V0.1 does not claim:

- generic sleeper detection;
- semantic malicious-intent classification;
- LLM-judge correctness;
- production sleeper resistance;
- long-horizon consolidation safety;
- automatic deletion of risky memory;
- contextual risk is factual truth;
- prior benign recall makes later use safe;
- contextual policy can override canonical lifecycle/scope refusal.

## Stop line

Do not expand this slice into:

- a general content moderation product;
- probabilistic trigger discovery;
- model-based semantic policy;
- automatic durable memory mutation;
- production certification;
- changing canonical storage state solely to demonstrate read-time containment.
