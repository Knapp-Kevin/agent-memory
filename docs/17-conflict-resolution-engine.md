# Conflict Resolution Engine

> Canonical requirement: [ADR-010](adr/ADR-010-conflict-resolution-is-a-separate-component.md)

## Purpose

Memory systems must tolerate contradiction without collapsing into either silent overwrite or permanent paralysis.

The Conflict Resolution Engine interprets conflicts among memories, sources, scopes, policies, and time windows, then proposes governed resolution paths.

Its core rule is:

> Conflict interpretation may be probabilistic. Conflict consequence must be governed.

## Why conflict is first-class

Persistent memory will inevitably encounter:

- new facts that contradict old facts
- preferences that change
- policies that supersede prior policies
- sources that disagree
- partial observations that support multiple explanations
- agent inferences that later fail
- memory that is valid in one scope but wrong in another

A system that cannot represent disagreement will eventually mistake recency, confidence, or repetition for truth.

## Conflict types

### Factual contradiction

Two claims cannot both be true under the same scope and time.

### Temporal supersession

Both claims may have been true, but at different times.

### Scope mismatch

Claims differ because they apply to different users, projects, tenants, environments, or domains.

### Source conflict

Sources disagree and neither has automatic authority.

### Policy conflict

Two rules or authorities overlap incompatibly.

### User correction conflict

A user correction challenges an inferred or stored memory.

### Estimator disagreement

Models, heuristics, or observers assign materially different confidence, trust, sensitivity, or causal interpretations.

### Representation conflict

An episodic record and a generalized semantic summary diverge.

### Procedure-version conflict

A learned procedure no longer matches the environment or policy under which it was formed.

### Concurrent write conflict

Two actors attempt to mutate the same shared durable state under overlapping scope and time.

This conflict is different from discovering contradictory memories after they are already durable. For shared writes, coordination must happen before commit so conflict resolution does not degrade into retrospective last-writer-wins cleanup.

## Conflict record

A conflict should be representable independently from either side:

```text
conflict_id
claim_refs
memory_refs
scope
time_window
conflict_type_candidates
source_refs
estimator_refs
estimator_versions
confidence_or_probability
uncertainty
policy_refs
status
detected_at
```

Do not destroy alternatives simply because one is currently favored.

## Probabilistic interpretation

Conflict detection may estimate:

- whether two claims truly contradict
- whether one supersedes the other
- whether a scope mismatch explains the difference
- source reliability
- causal explanations
- likelihood that a claim is stale

Multiple hypotheses may remain active.

Example:

```text
P(factual_contradiction) = 0.20
P(temporal_supersession) = 0.65
P(scope_mismatch) = 0.15
```

The exact mathematical representation is implementation-specific.

The doctrine requirement is that uncertainty not be collapsed prematurely.

## Governed resolution outcomes

Policy may permit outcomes such as:

```text
retain_both
split_scope
mark_disputed
request_more_evidence
require_external_verification
prefer_temporally_newer
prefer_authoritative_source
correct_preserve_history
demote
archive_superseded
block_canonical_use
escalate
```

The estimator proposes. Policy determines which consequences are permissible.

## Resolution precedence

Some evidence may carry explicit authority.

Examples:

- user correction about the user's own stated preference
- signed policy superseding an older policy
- verified repository state replacing an inferred build-state memory

Precedence must be scoped.

```text
human correction authority in scope X
!= universal factual authority in all scopes
```

## Historical truth versus current truth

Conflict resolution must preserve history.

Wrong:

```text
old address = A
new address = B
therefore erase A
```

Correct:

```text
A valid until T
B valid from T
current=B
historical=A preserved
```

This distinction is central to temporal memory.

## Correction versus supersession

Use correction when the earlier memory was wrong within its claimed scope/time.

Use supersession when the earlier memory was valid but no longer current.

```text
correction -> prior claim was erroneous or incomplete
supersession -> prior claim was valid then, newer state applies now
```

## Scope splitting

Sometimes conflict should create multiple scoped memories rather than a winner.

Example:

```text
production uses endpoint A
staging uses endpoint B
```

A flat overwrite would destroy useful truth.

## Conflict and source trust

Source trust may influence conflict ranking, but must not dominate automatically.

Consider:

- source domain competence
- origin integrity
- independence
- recency
- directness
- authoritative scope
- corroboration
- uncertainty

A highly trusted source can still be wrong or out of scope.

## Conflict and saturation

Saturation should not make a claim immune to correction.

A highly saturated memory may deserve stronger audit handling because more downstream systems depend on it, but that is consequence management, not factual immunity.

## Conflict and crystallized memory

Crystallized memory remains disputable.

When a credible conflict is introduced:

```text
Crystallized
  -> Disputed or Stale
  -> verification / resolution
  -> Corrected / Reconciled / split scope / restored
```

Canonical use may be restricted while the dispute remains unresolved.

## Conflict and action

An agent may need to act before conflict is fully resolved.

Policy can define bounded behavior:

```text
low consequence -> proceed with warning
medium consequence -> choose reversible action
high consequence -> require verification
critical consequence -> abstain or escalate
```

Uncertainty does not require universal paralysis. It requires proportional consequence handling.

## Shared durable writes: coordinate before commit

For concurrent mutation of shared durable memory, the overwrite/conflict boundary is resolved before the substrate mutation rather than after it.

Proposed [ADR-024](adr/ADR-024-shared-memory-writes-require-prewrite-claims.md) defines the candidate contract. A writer must first hold a valid claim, lease, lock, compare-and-swap reservation, single-writer queue position, transactional reservation, or equivalent coordination mechanism that binds at least:

```text
actor
task
scope
target memory
mutation class
authority basis
state snapshot
issued time
expiry / validity
```

A coordination claim means only:

> this actor currently owns the bounded opportunity to attempt this shared mutation.

It does not mean:

```text
claim acquired == PAMA allow
claim acquired == truth
claim acquired == overwrite authority
claim acquired == durable mutation committed
```

Immediately before commit, the implementation must revalidate the claim against current state and the actual proposal. At minimum:

- an expired lease fails closed;
- a stale state snapshot fails closed;
- an unauthorized authority basis fails closed;
- a conflicting active claim prevents a second writer from committing silently;
- actor, task, scope, target, and mutation mismatches fail closed;
- PAMA or the applicable mutation-authority policy still evaluates the proposal after coordination succeeds.

This creates an explicit ordering:

```text
proposal intent
  -> pre-write coordination claim
  -> conflict / lease / state validation
  -> PAMA authority envelope
  -> permitted action selection
  -> durable mutation or refusal
  -> audit / conflict evidence
```

A valid claim that later encounters a PAMA `block` remains blocked. Coordination cannot launder authority.

Successful, rejected, conflicting, stale, expired, and unauthorized claims should remain audit evidence. The reference implementation in `reference/agentmem_ref/runtime/write_claims.py` demonstrates one exact-scope lease mechanism; it is evidence for the contract, not a requirement that implementations adopt that mechanism.

## Deterministic substrate

The following should remain stable:

- claim identities
- conflict identities
- evidence/provenance links
- state-transition validity
- policy outcome semantics
- history preservation
- ledger records

Conflict interpretation need not be deterministic.

## Anti-patterns

### Newest wins

Recency alone does not prove truth.

### Most repeated wins

Repetition may share one origin.

### Highest confidence wins

Model confidence is not authority.

### Trusted source always wins

Trust is scoped evidence, not universal truth.

### Deterministic classifier as truth oracle

A reproducible conflict label can still be wrong.

### Silent merge

Combining conflicting memories into a summary without preserving the dispute destroys evidence.

### Coordinate after overwrite

Detecting two writers only after one has silently replaced the other's durable state is not pre-write conflict control. The competing authority must be resolved or rejected before the mutation becomes durable.

## Conformance cases

### Temporary failure misremembered as permanent

Multiple observations support both transient and persistent explanations.

Expected:

```text
alternatives remain visible until evidence resolves them
```

### User preference changed over time

Expected:

```text
old preference preserved historically
new preference becomes current within scope
```

### Scope mismatch

Expected:

```text
claims split by scope instead of one overwriting the other
```

### High-confidence wrong claim versus verified artifact

Expected:

```text
confidence does not overrule authoritative evidence within its scope
```

### Two uncertain estimators disagree

Expected:

```text
disagreement preserved
policy may request evidence or abstain
```

### Concurrent corrections

Expected:

```text
conflict is explicit
silent last-writer-wins is prohibited for durable state
```

### Concurrent shared write claims

Expected:

```text
first valid claim may acquire coordination
second conflicting claim is rejected before durable commit
stale / expired / unauthorized claims do not reach mutation
valid claim still cannot override a stricter PAMA outcome
all claim outcomes remain auditable
```

Executable reference fixtures:

- `shared-write-valid-claim.json`
- `shared-write-conflicting-claim.json`
- `shared-write-stale-claim.json`
- `shared-write-unauthorized-claim.json`

## Research signals

- [Belief Memory: Agent Memory Under Partial Observability](https://arxiv.org/abs/2605.05583) challenges deterministic one-conclusion storage and supports retaining alternative hypotheses under uncertainty.
- [Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers](https://arxiv.org/abs/2603.07670) identifies contradiction handling and causally grounded retrieval among important memory-system concerns.
- [From Agent Traces to Trust](https://arxiv.org/abs/2606.04990) reinforces provenance and evidence tracing as prerequisites for explaining and recovering from agent errors.

## Doctrine

Conflict is not a defect in memory. Hidden conflict is.

A mature system preserves disagreement long enough to resolve it responsibly, and it separates the uncertain question **“what does this conflict mean?”** from the governed question **“what are we allowed to change because of it?”**
