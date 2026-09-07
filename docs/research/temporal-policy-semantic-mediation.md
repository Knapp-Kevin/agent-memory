# Temporal Policy Semantic Mediation Research

Status: research finding under #255 and parent #67. This document is not canonical doctrine.

## Question

How should Agent Memory provide remembered historical and current context to temporal and authorization systems when the meaning, schema, validity, and scope of memory can evolve after the original event occurred?

The useful question is not whether Agent Memory should adopt Dogwood, Cedar, or Cedarling. It is whether those systems expose a reusable boundary that Agent Memory must represent more precisely.

## Research result

The current evidence supports a generic boundary:

> **A policy consumer should receive a versioned, currentness-aware semantic projection of memory, not canonical memory itself, and consequential use of that projection requires evidence that the projection is compatible with the exact schema, policy artifact, temporal capabilities, and isolation assumptions under which the consumer will evaluate it.**

This result extends existing Agent Memory projection and currentness work. It does not replace it.

The architecture is better described as **governance-preserving semantic mediation** than normalization. Agent Memory should not flatten all retained state into one universal data model. It should preserve distinctions internally and export the smallest truthful, current, scoped, provenance-preserving representation a consumer needs.

```text
canonical Agent Memory
  identity
  provenance
  event/valid time
  scope/isolation
  schema/model version
  correction/supersession/revocation
  derivation + currentness
        |
        v
versioned governed projection
        |
        v
projection compatibility/currentness gate
        |
        +--> temporal event projection -> temporal policy trace
        |
        +--> typed entity/context projection -> authorization PDP
        |
        v
external decision + decision evidence
        |
        v
existing monotonic composition
        |
        v
external evidence normalization / future memory
```

The consumer-side trace/cache remains derived state. It is not a second canonical Agent Memory history.

## Exact public Dogwood research boundary

Research is pinned to the public repository:

- repository: `dogwood-policy/dogwood`
- public commit: `c6237c88099b3f492ecc5fcee42df06a19224b97`
- license: Apache-2.0
- public role: reference parser and interpreter
- current public releases: none

The public repository explicitly describes its current source as a sanitized synchronization from an internal Dogwood source and states that internal git history is not included. This matters to Agent Memory in a narrow way:

```text
published public contract -> usable evidence
unpublished/internal capability -> unknown
unknown future capability -> not an implementation prerequisite
```

Agent Memory therefore should not freeze its architecture around assumptions about unpublished Dogwood behavior. Any executable Dogwood comparator should pin the exact public source revision and require revalidation when the public contract changes.

This is not a criticism of Dogwood's publication model. It is ordinary evidence discipline at an interoperability boundary.

## Dogwood responsibility analysis

### Stateful temporal policy is real and distinct

Dogwood extends Cedar-style authorization with bounded, past-only temporal expressions over an event history. Its public language supports temporal operators including `formerly`, `previous`, and `since`, all under bounded look-back windows.

Dogwood's `Authorizer` is stateful. Each ingested event folds into accumulated history. Some event kinds are decision points and others are history-only.

This creates a responsibility Agent Memory's existing OPA/Cedar external-policy comparators do not exercise:

```text
current request policy
!=
policy over a bounded historical trace
```

### Event schema is a projection surface

Dogwood does not impose one fixed event model. Its event-schema DSL derives event signatures from an action schema and allows custom event kinds, input/output projections, principal/resource fields, nested fields, and decision/history classification.

That makes the event schema a natural adapter boundary.

Agent Memory does not need to make Dogwood's trace canonical. Instead it can project governed historical events into a target event schema when:

- the source event remains appropriate for the requested projection;
- the target schema is known and compatible;
- scope/isolation requirements are satisfied;
- required temporal capability exists;
- the projection identity and derivation remain reconstructable.

### Historical truth and current applicability are different

A memory event can remain historically true while becoming unsafe to rely on as current context.

Example:

```text
T1: approval occurred under policy P1
T2: approval authority revoked
T3: current action resembles T1
```

The T1 event should not be deleted from history merely because its current applicability changed. Dogwood may still be able to match the historical event. Agent Memory therefore must not let `temporal match = true` erase currentness state.

A safe projection can express or bind the current applicability of the event separately from the historical event itself, or omit the event from a projection whose declared purpose requires current applicability. Which strategy is used is profile-specific; the invariant is that historical match does not manufacture current authority.

### Temporal window is a capability, not evidence absence

Dogwood requires temporal operators to use bounded windows and applies a configured maximum look-back window. The default public event schema uses a 24-hour maximum, although the event schema can raise it.

If an Agent Memory use case requires 30 days of history while the target Dogwood service allows only 24 hours, the correct result is:

```text
capability mismatch
```

not:

```text
no matching event exists
```

Treating an execution limitation as negative historical evidence would be a semantic error.

### Pins expose an isolation contract and a failure mode

Dogwood's public event schema supports pins that force event predicates to correlate with the current request. When the same symmetric pin is applied universally across every event kind, the language provides key-local temporal semantics and a partition guarantee.

The public documentation also exposes an important negative path: a pin that is not universal or not symmetric remains valid but silently keeps global-trace semantics. It does not warn that the partition guarantee was lost.

That creates a concrete integration invariant:

> An Agent Memory adapter must not infer target isolation merely because a Dogwood event schema contains a pin. A claimed isolation strategy must be validated against the actual target event schema and bound into compatibility evidence.

For cross-tenant or cross-project memory this is consequential.

### Information providers are another projection seam

Dogwood information providers can inject deterministic values into Cedar context. Provider declarations define argument and output types, and current public validation resolves field paths against the schema for the actions a rule can reach.

This is useful for Agent Memory because some memory-derived current facts may be better supplied as current policy context than replayed as events.

The distinction should remain explicit:

```text
historical event projection
!=
current provider/context projection
```

A remembered event such as `approval occurred` belongs naturally in history. A current derived fact such as `approval authority is currently revoked` may be better represented as current context. Combining both lets a temporal policy reason over history without pretending the historical record already contains today's currentness.

Agent Memory should not require Dogwood's Rhai provider implementation in core. The generic contract is semantic; a Dogwood adapter owns the concrete provider/event representation.

### Dogwood reference interpreter is not production enforcement

The current public README explicitly limits the reference interpreter. Among the documented production concerns are:

- trusted event timestamps;
- event authentication;
- event-field/action naming consistency;
- durable/bounded trace management;
- sensitive trace retention/purge;
- audit logging;
- multi-tenant isolation;
- provider sandboxing and network exposure;
- policy validation.

These are not reasons to avoid Dogwood. They are reasons not to let a reference comparator prove more than it actually proves.

## Cedar responsibility analysis

Cedar makes the schema boundary unavoidable.

A Cedar schema describes the application entity types, attributes, actions, principal/resource applicability, and request context expected by policies. Cedar validation checks policies against that schema before authorization.

The Cedar documentation explicitly warns that changing the schema may invalidate policies that were previously valid. Policies that error at authorization time can be ignored for the decision, so an application that changes its data model without revalidating policy can produce unexpected behavior.

For Agent Memory this means:

```text
domain-schema mutation
-> policy-consumer schema compatibility changes
-> prior policy validation cannot be assumed current
```

The safe boundary is not merely a JSON serializer. It must be able to say whether the current Agent Memory projection is valid under the exact target authorization model.

## Cedarling responsibility analysis

Cedarling adds several operational surfaces around Cedar that are useful to the same architecture without becoming canonical memory.

### Dynamic context data

Cedarling can accept dynamic pushed data with TTL and exposes it to policies under `context.data`.

That sounds like a natural memory integration seam, but the public contract imposes an important restriction: the Cedar schema must explicitly declare `data` and every field shape that may be used. Cedar does not accept arbitrary untyped records here.

Therefore:

```text
Agent Memory can evolve domain knowledge freely under its own governance
!=
Cedarling can consume arbitrary newly discovered fields without policy-schema evolution
```

A newly discovered Agent Memory domain field may require a target Cedar schema change, policy revalidation, and a new compatibility evaluation before the field is safely projected to Cedarling.

### Context precedence

Cedarling merges context data with this precedence:

```text
inline request context
>
pushed context data
>
default context
```

This creates a binding requirement. A decision receipt cannot truthfully claim it evaluated the Agent Memory-projected value merely because that value was pushed into Cedarling. If an inline request shadows the key, the decision identity/evidence must reflect the value actually evaluated.

### Policy-store and decision evidence

Cedarling policy stores bind policies, Cedar schema, trusted issuers, optional default entities, and store identity/version metadata. Cedarling decision logs can record policy-store identity/version, request identity, action/resource, decision, diagnostics, and pushed-data information.

Those are useful external decision-evidence fields.

They are not:

- standing memory authority;
- proof of execution or enforcement;
- proof that Agent Memory schema compatibility remained current;
- independent human adjudication.

They fit behind the existing external evidence and monotonic decision-composition boundaries.

## Existing Agent Memory coverage

This research does not require a new architecture from zero.

### ADR-029 / Governance Context Projection

Already establishes:

```text
canonical Agent Memory
-> vendor-neutral derived governance context
-> consumer-specific adapter
```

and explicitly prohibits projection from becoming final decision authority.

### External Enforcement Decision Projection

Already binds current policy evaluation to exact Agent Memory input identity and proves monotonic composition against real OPA and Cedar:

```text
local deny + external allow -> deny
local review + external allow -> review
local allow + external deny -> deny
```

The external decision remains separate from enforcement/execution evidence.

### ADR-014 and progressive domain-schema discovery

Agent Memory already treats schemas as governance and separately researches runtime domain ontology evolution. Domain-schema mutation can require migration and projection invalidation/rebuild without rewriting historical evidence.

### Derivation currentness

Agent Memory already has the right historical/current split:

```text
historical derivation remains immutable
+
new currentness evaluation says current / revalidation_required / unknown
```

The missing piece is applying this discipline specifically at an outbound semantic projection boundary.

## Identified gap: projection compatibility/currentness

The current generic external-policy seam binds the current action to `input_identity` and preserves provider policy identity in adapter evidence. It does not yet define a reusable object proving that the memory-derived projection remains semantically compatible with the target consumer's current schema and capabilities.

A new compatibility/currentness evaluation should bind, where applicable:

```text
source memory refs / root refs
source domain-schema ref + digest
source currentness evaluation ref + state
projection profile + version
projection identity + digest
target consumer kind + version/source pin
target action/policy schema digest
target event-schema digest
target policy-store/policy-artifact identity
temporal horizon requirement + target capability
isolation strategy + validation evidence
compatibility status
reason codes
evidence refs
```

Candidate states:

```text
current
migration_required
incompatible
unknown
```

Interpretation:

- `current`: supplied evidence establishes compatibility for this exact projection/target contract;
- `migration_required`: a known semantic/schema change requires target projection/schema/policy work before current use;
- `incompatible`: a concrete contradiction prevents this projection from satisfying the target contract;
- `unknown`: required evidence is missing or cannot establish compatibility.

`unknown` is never a synonym for current.

The compatibility object has no authority effect. It only establishes whether a projection is eligible to be considered current input to the external consumer under the declared contract.

## Four contracts, not one integration

The research resolves the initial architecture into four separable contracts.

### 1. Memory-to-policy context projection

Current, minimized memory-derived facts/precedent for a policy consumer.

Existing Governance Context Projection provides much of this surface.

### 2. Temporal-event projection

A reconstructable event representation shaped for a temporal consumer such as Dogwood.

It carries historical event semantics and projection provenance but does not become the canonical event log.

### 3. Projection compatibility/currentness evaluation

The newly identified primitive. It proves or declines current compatibility between a projection and the exact target schema/capability/isolation assumptions.

### 4. Policy-decision evidence return path

External decision/result evidence comes back through existing decision/evidence normalization boundaries and may inform future memory under normal provenance, scope, lifecycle, and PAMA rules.

It does not become truth or human authority merely because it came from a deterministic policy engine.

## Required adversarial matrix

| Case | Unsafe interpretation | Required result |
|---|---|---|
| Agent Memory domain schema changed, Dogwood/Cedar schema old | old target schema is "close enough" | `migration_required` or `incompatible` |
| historical approval still in trace, authority later revoked | temporal match means approval is current | preserve history, currentness blocks authority inference |
| Dogwood pin exists only on request events | pin means history is tenant-partitioned | isolation guarantee rejected |
| action/field naming mismatch | no match means safe/no prior event | incompatible input/schema evidence |
| target policy/schema digest changed | old external decision can be replayed | stale binding rejected |
| required 30d history, target max window 24h | no event means event never happened | capability mismatch |
| schema mutation rebuilds projection | mutate old projection/history in place | new projection identity, old evidence immutable |
| consumer trace/cache survives source purge | canonical forgetting complete | no deletion-completeness claim |
| external ALLOW conflicts with PAMA deny/review | external policy can loosen memory authority | PAMA remains stricter result |
| cross-tenant events visible to temporal trace | correlation is probably sufficient | explicit isolation strategy required |
| provider/context value unavailable | missing value can be treated as false/safe | unknown or consumer failure posture, not permissive currentness |
| Dogwood public source revision changes | previous comparator proof still covers new source | revalidation required |
| Cedarling inline value shadows pushed value | pushed Agent Memory value was evaluated | evaluated context identity must reflect winning value |
| Cedar schema changes without policy revalidation | old validation remains sufficient | compatibility not current |
| source currentness is unknown | probably current | unknown remains non-current |
| deterministic policy outcome recorded repeatedly | repeated policy allows become human precedent/grant | preserve policy provenance; no authority inflation |

## Decision

The research supports a new ADR rather than only editing ADR-029.

ADR-029 answers:

> Is a governance projection canonical memory or authority?

The new decision answers:

> When may an evolving memory-derived projection be treated as semantically current for an external policy/temporal consumer?

Those are related but independently falsifiable invariants.

Proposed ADR-030 should therefore establish:

> **Temporal/policy consumers receive versioned governed projections, and consequential use requires current compatibility with the exact target schema, policy identity, capabilities, and isolation assumptions. Historical projection evidence remains immutable when compatibility changes.**

## Implementation direction

A Python-first reference implementation is appropriate because this is an Agent Memory contract, not a Dogwood implementation.

The smallest useful slice is:

1. JSON Schema for a policy-projection compatibility evaluation;
2. deterministic Python evaluator;
3. adversarial fixtures for schema drift, currentness drift, target drift, isolation failure, and temporal capability mismatch;
4. a Dogwood-specific adapter/comparator that maps exact public Dogwood schema/capability evidence into the generic contract;
5. focused exact-head evidence;
6. a real Dogwood source comparator when practical, pinned to the public commit above;
7. wiki/visual documentation only after executable evidence establishes the boundary.

Cedar and Cedarling should remain comparison/reference surfaces for this slice rather than adding duplicate runtime dependencies. Existing Cedar execution already proves the generic external-decision composition seam.

## Non-claims

This research does not establish:

- production Dogwood conformance;
- production Cedarling integration;
- one universal memory/policy schema;
- automatic domain-schema migration;
- automatic policy rewriting;
- that every Agent Memory event belongs in a temporal policy trace;
- that a temporal match is memory truth or authority;
- that a policy decision is enforcement evidence;
- that the public Dogwood repository describes unpublished/internal capabilities;
- that Rust should become Agent Memory's default implementation language.

## Stop line

Preserve semantic complexity where it matters. Export only a bounded, versioned, reconstructable view, and require evidence that the view still means what the receiving policy system thinks it means before consequential use.
