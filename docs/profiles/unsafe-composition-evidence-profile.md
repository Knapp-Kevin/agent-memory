# Unsafe Multi-Memory Composition Evidence Profile

Status: V0.1 evidence profile for #206.

## Purpose

This profile binds the existing Agent Memory set-level composition gate to the named unsafe-composition fixture and to the repository D/F/H/R/P evidence model.

It does **not** introduce a new composition policy engine.

The implementation already exists in:

- [`../../reference/agentmem_ref/runtime/composition.py`](../../reference/agentmem_ref/runtime/composition.py)
- the completed isolation/composition work from #68 and #132.

The evidence boundary is:

```text
memory A individually admitted
+
memory B individually admitted
!=
A + B permitted as one active context
```

Candidate-level admission and set-level context composition are distinct governed decisions.

## Structural fixture

[`../../fixtures/unsafe-multi-memory-composition.json`](../../fixtures/unsafe-multi-memory-composition.json) requires:

```text
individual_candidates_may_pass = true
combined_context_admitted = false
composition_governance_runs = true
```

and names these invariants:

```text
item_level_admission_not_sufficient
composition_risk_checked
unsafe_combination_not_injected
```

The V0.1 harness executes those statements rather than treating fixture validation as behavioral proof.

## Existing set-level gate

`evaluate_composition(...)` consumes:

```text
composition candidates
actual admitted memory refs
explicit composition constraints
```

Each candidate preserves:

```text
memory_ref
domain_refs
```

A constraint preserves:

```text
constraint_ref
prohibited_domain_set
reason
```

A proposed composition is rejected if:

- a requested candidate was not admitted by ordinary governed recall;
- candidate domain provenance is unresolved;
- a memory reference is duplicated;
- an explicit prohibited domain set is fully present in the proposed context.

The gate does not invent a universal rule that memories from different domains may never compose.

## Explicit policy is required

The behavioral harness proves the same two individually admitted memories are allowed when no set-level constraint applies.

```text
same memories
same recall admission
no composition constraint
-> composition allowed
```

It also proves an unrelated constraint does not block them.

Therefore the security claim is bounded:

```text
explicit current constraint + matching composition
-> block
```

not:

```text
different domain refs
-> always block
```

## Fixture-linked behavioral sequence

The harness in [`../../reference/agentmem_ref/harness/unsafe_composition_harness.py`](../../reference/agentmem_ref/harness/unsafe_composition_harness.py) executes:

```text
memory A / domain red
 -> governed write
 -> governed recall
 -> admitted

memory B / domain blue
 -> governed write
 -> governed recall
 -> admitted

A + B
 -> proposed composition
 -> explicit red+blue constraint
 -> existing composition gate
 -> cross_domain_composition_prohibited
```

The observation preserves:

```text
candidate refs
individually admitted refs
domain refs
violated constraint refs
blocking reason
assembled-context surface
downstream-influence surface
```

## Final context and influence boundary

A rejected composition produces:

```text
assembled_context = []
downstream_influence = []
```

These are bounded identity surfaces in the reference harness. They do not model an entire downstream agent runtime.

Their purpose is to make the important consequence explicit:

```text
composition rejected
!= merely a warning attached to a still-injected context
```

The blocked set is not eligible for context assembly or downstream influence in this proof.

## Ordering and ranking cannot bypass the gate

Domain combinations are set-like. Tuple order carries no hierarchy.

The harness reverses:

- candidate order;
- admitted-ref order;
- prohibited-domain declaration order.

The same explicit red+blue policy still rejects the composition.

This means a ranker, retriever ordering difference, or caller tuple order cannot transform a prohibited set into an allowed one merely by permutation.

## Ordinary recall remains authoritative

The composition gate receives the memory refs actually admitted by governed recall.

It cannot reintroduce a candidate that recall rejected.

The harness marks one candidate disputed and repeats ordinary recall. That memory remains discoverable but is no longer admitted. A later composition attempt with both candidates then fails with:

```text
composition_candidate_not_admitted
```

Thus:

```text
composition policy may further restrict admitted candidates
!= composition may repair or widen a recall refusal
```

## Other fail-closed paths

The existing gate and V0.1 evidence cover:

### Duplicate references

```text
same memory requested twice
-> duplicate_memory_reference
-> reject
```

### Unresolved scope/domain provenance

```text
candidate has no domain refs
-> composition_candidate_scope_unresolved
-> reject
```

### Unadmitted candidate

```text
candidate requested for composition
candidate absent from admitted_memory_refs
-> composition_candidate_not_admitted
-> reject
```

### Unrelated constraint

```text
red + blue candidates
red + green prohibition
-> no match
-> allowed
```

This last case is important because it prevents the evidence harness from turning one named unsafe pair into a generic cross-domain ban.

## What this profile does not detect

The V0.1 gate evaluates explicit deterministic constraints over candidate/domain provenance.

It does not claim to discover every semantically unsafe combination.

For example, it does not by itself infer that two individually harmless natural-language facts reconstruct a secret or create a dangerous instruction chain. A deployment may place probabilistic or learned composition-risk analysis before an explicit governed consequence, but such an estimator remains evidence/proposal input rather than authority.

The general repository rule still applies:

```text
probabilistic discovery may vary
governance consequence remains bounded
```

## Evidence depth

The dedicated report reuses the repository-wide D/F/H/R/P schema:

```text
D = governed recall/isolation doctrine + this profile
F = unsafe-multi-memory-composition fixture
H = fixture-linked behavioral composition harness
R = explicitly unproven by this slice
P = explicitly unproven
```

Existing composition implementation and unit tests are not silently relabeled as runtime `R` evidence. This slice improves explicit evidence accounting only.

`R` would require separately governed runtime evidence bound to an exact implementation/runtime environment.

`P` would require separately supplied production evidence under a named deployment/configuration.

## Privacy and minimization

The composition evidence needs identity and policy refs, not raw memory contents.

The harness/report preserve:

- candidate refs;
- domain refs;
- admission state;
- constraint refs;
- reason;
- evidence result.

They do not require raw prompts, hidden reasoning, or complete memory bodies.

## Deployment profiles

### L: local

A local runtime can apply explicit set-level constraints after ordinary recall. The gate remains useful even when all memory is stored on one machine.

### T: team / multi-tenant

Set-level composition is especially important where multiple legitimate project/domain routes may be simultaneously visible to a requester. Individual access to each item does not automatically authorize their joint context.

### E: enterprise

Policy/constraint identity and blocking reasons should remain reconstructable so a rejected composition can be audited without retaining sensitive assembled content.

### H: high assurance

The exact admitted set, candidate domain provenance, current constraint refs, set-level result, and final context/influence surface should remain independently reconstructable.

## Non-claims

V0.1 does not claim:

- universal unsafe-composition detection;
- universal prohibition on cross-domain composition;
- semantic content safety classification;
- model-based composition risk correctness;
- runtime `R` evidence from unit/reference execution;
- production `P` evidence;
- external security certification.

## Stop line

Do not redesign the #68/#132 composition semantics in this evidence slice. If future work needs learned or semantic composition-risk detection, it should feed the existing governed set-level boundary rather than replacing it with an estimator decision.
