# ADR-022: Memory Isolation Domains and Controlled Boundary Crossing Are First-Class

## Status

Accepted

## Context

Agent Memory already treats actor scope, consent, delegation, tenancy, project/repository scope, purpose limitation, destination, and sharing authority as first-class governance concerns through ADR-016 and the actor-scope contract.

That is necessary but not sufficient.

A single agent may work across multiple projects, repositories, tasks, sessions, purposes, or compartments. Multiple agents may share one physical memory service while requiring strict logical separation. Conversely, one logically shared memory space may span multiple physical stores and projections.

Without an explicit isolation-domain model, implementations can accidentally collapse:

```text
same agent
same storage service
same tenant
high semantic relevance
```

into an assumption that memory is safe to recall everywhere that agent operates.

That assumption is invalid.

The architecture therefore needs a stronger statement than "memory has scope metadata." It needs to express **where retained state is allowed to exist, be recalled, be combined, be transformed, and cross boundaries**.

The same problem appears in shared memory. A shared memory space is not the absence of isolation. It is a deliberately broader isolation domain with explicit membership, ownership, admission, mutation, and re-sharing rules.

## Decision

Agent Memory will treat **memory isolation domains** as first-class governance boundaries.

An isolation domain is a logical authority boundary over retained state. It is independent of physical storage topology.

```text
physical store != isolation domain
```

One physical store may contain many isolation domains. One logical isolation domain may span multiple stores, indexes, graphs, files, projections, or services.

The architecture will preserve the following rules.

### 1. Same agent does not imply same memory scope

```text
same_agent
!= same_project
!= same_task
!= same_purpose
!= permission_to_recall
```

An agent identity is not itself a universal memory namespace.

A memory valid for one project, task, session, workspace, or purpose is not automatically admissible into another context merely because the same agent is acting in both.

### 2. Isolation domains may be nested or intersecting

Implementations may need dimensions including:

```text
tenant
principal / user
organization
team
agent
workspace
project
repository
task
session
purpose
shared memory space
external destination
```

Agent Memory does not require one universal fixed hierarchy.

The required invariant is that consequential use can resolve the domain or domain set that authorizes it.

### 3. Recall resolves target domain before admission

Governed recall must identify the requesting context, including its relevant isolation domain, before admitting retained state into active context.

Retrieval relevance cannot authorize a crossing:

```text
semantic_relevance = 1.0
same_agent = true
wrong_project = true
=> block
```

Where candidate generation itself would disclose prohibited content or metadata to an untrusted retriever, model, or caller, enforcement must occur before candidate generation rather than relying only on a post-retrieval filter.

### 4. Boundary crossing is a governed consequence

Moving information from one isolation domain into another is not merely retrieval, copying, or serialization.

Operations such as:

```text
share
export
import
copy
promote_scope
summarize_for
derive_for
inherit
publish
```

may cross an authority boundary and therefore require governance appropriate to their consequence.

A consequential crossing should bind enough information to reconstruct:

```text
source domain
destination domain
actor / principal
purpose
representation
sensitivity
consent / delegation
PAMA decision
policy version
provenance
expiry / revocation
outcome
receipt
```

### 5. Derived state does not silently broaden scope

Transformation does not erase authority obligations inherited from source state.

A summary, embedding, graph edge, extracted entity, index entry, cache, materialized view, or synthesized memory derived from restricted input must not acquire broader authority merely because the transform omitted the original scope metadata.

The default model to validate is:

```text
derived_allowed_audience <= intersection(source_allowed_audiences)
derived_allowed_purpose  <= intersection(source_allowed_purposes)
derived_restrictions     >= union(source_restrictions)
```

An intentional broadening requires a separate governed scope-promotion decision.

### 6. Composition may create a new boundary failure

Memories that are individually admissible may be prohibited in combination.

Examples include:

- aggregate sensitivity
- reconstruction of restricted information
- project or compartment mixing
- purpose conflict
- cross-tenant composition
- contractual or regulatory separation

Domain provenance must therefore survive composition long enough for composition governance to evaluate the combined context.

### 7. Shared memory is a governed isolation domain

A shared memory space must have explicit governance rather than being modeled as globally visible memory.

Where applicable, a shared space should identify:

- owning principal
- members
- allowed readers
- allowed writers
- admission policy
- purpose
- sensitivity constraints
- correction authority
- deletion authority
- re-sharing rules
- revocation behavior

Membership creates candidacy for use. It does not create universal admission or re-sharing authority.

### 8. Scope reduction, correction, revocation, and deletion propagate where required

If memory legitimately crossed domains, later governance events may require propagation across those crossings and their derived state.

Relevant events include:

- correction
- dispute
- consent revocation
- delegation expiry
- scope reduction
- deletion / purge

This decision therefore composes directly with canonical-versus-derived-state work and deletion-residue analysis.

### 9. PAMA evaluates scope crossing as consequence

PAMA remains the authority framework for durable or influential memory mutation.

A scope-crossing decision should consider, where relevant:

- source domain
- destination domain
- audience or fan-out expansion
- purpose change
- sensitivity
- persistence
- reversibility
- shared/canonical status
- downstream authority
- representation form

Prior authorization inside the source domain does not automatically authorize broader use elsewhere.

### 10. Unknown scope does not become broad scope

For high-consequence recall, sharing, or mutation:

```text
unknown domain != global permission
uncertain membership != authorized membership
```

Policy should block, narrow, verify, or require review rather than assuming compatibility.

## Relationship to ADR-016

ADR-016 remains canonical and is not superseded.

ADR-016 establishes that actor scope, consent, delegation, tenancy, project/repository scope, purpose, and re-sharing rights are required governance concerns.

ADR-022 establishes the next abstraction:

> Those dimensions must be able to resolve into **logical isolation domains and controlled crossings** so the system can demonstrate that memory did not bleed between contexts that happen to share an agent or storage substrate.

In short:

```text
ADR-016: what scope/authority dimensions must be represented
ADR-022: how those dimensions form memory isolation boundaries and crossings
```

## Relationship to governed recall

The governed recall planner remains responsible for context admission.

ADR-022 requires that recall planning be able to distinguish at least:

```text
candidate visibility
recall permission
context admission
derivation permission
share/export permission
downstream action influence
```

An implementation may collapse some of these capabilities where policy proves them equivalent. It must not assume they are equivalent by default.

## Relationship to multi-agent shared memory

The future multi-agent shared-memory protocol treats a shared space as a governed isolation domain.

Agent-to-agent sharing therefore becomes a specific instance of controlled boundary crossing rather than a separate exception to the isolation model.

## Relationship to P4 canonical / derived / projection work

Isolation metadata and domain provenance must survive enough of the derivation graph to support:

- correction propagation
- scope reduction
- revocation
- transitive deletion
- residue detection
- governed rebuild

A derived projection that loses its source-domain constraints is both a provenance defect and a potential authority-laundering path.

## Consequences

### Positive

- prevents same-agent cross-project and cross-task memory bleed
- makes shared memory explicit rather than ambient
- separates logical governance from physical storage layout
- gives PAMA a principled way to reason about audience/purpose expansion
- makes task/project switching auditable
- improves multi-agent tenancy and shared-memory semantics
- strengthens deletion/correction propagation across copied and derived state
- supports heterogeneous storage architectures without weakening scope governance

### Negative

- increases scope metadata and policy complexity
- may require domain-aware retrieval or pre-filtering for sensitive stores
- requires provenance through derivation and sharing boundaries
- complicates task switching and context reuse
- makes shared-memory membership and revocation state explicit operational concerns
- may expose that existing storage/index products cannot enforce isolation without adapter-owned sidecars or prefilters

## Alternatives considered

### Use one physical store per agent/project/task

Rejected as doctrine.

Physical separation can be useful defense-in-depth, but it is not a general semantic model. It scales poorly, does not address derived or exported copies, and cannot represent intentionally shared memory cleanly.

### Treat project/task as ordinary metadata filters

Rejected.

A filter is an implementation mechanism. The architecture needs an authority boundary with explicit crossing semantics, especially where retrieval, derivation, composition, or export can bypass simple filters.

### Treat agent identity as the silo

Rejected.

One agent may operate under multiple projects, tasks, users, purposes, or delegated roles. Agent identity alone is too coarse.

### Treat shared memory as an exception outside the silo model

Rejected.

Shared memory has ownership, membership, mutation, recall, correction, deletion, and re-sharing boundaries. Modeling it as a governed domain is simpler and safer than inventing a separate permission universe.

## Acceptance evidence

ADR-022 is **Accepted** because the repository can express and test the decision without relying on unproven cross-architecture runtime claims.

Minimum evidence is satisfied by:

1. canonical contract: [`../41-memory-isolation-domains-and-governed-crossing.md`](../41-memory-isolation-domains-and-governed-crossing.md);
2. ADR-016 relationship: this ADR and the canonical contract preserve ADR-016 as the scope/authority-dimension contract rather than duplicating it;
3. machine-readable boundary state: [`../../schemas/memory-unit.schema.json`](../../schemas/memory-unit.schema.json) and the isolation-domain schema surface;
4. governed recall target context: the reference governed adapter resolves target isolation-domain, project, and task context before admission;
5. crossing evidence: the boundary-crossing decision/receipt schema and reference emitter bind source/destination domains, PAMA/policy evidence, and outcome;
6. derived-state semantics: scope propagation uses audience/purpose intersection, accumulated restrictions, and fail-closed handling for incompatible source scopes;
7. critical same-agent project/task fixtures and executable reference tests;
8. unauthorized scope-promotion fixture and PAMA `scope_expansion` handling;
9. shared-memory member/non-member recall and revocation tests, including `fixtures/shared-space-non-member-recall.json`;
10. reconciled [`../future/multi-agent-shared-memory-protocol.md`](../future/multi-agent-shared-memory-protocol.md); and
11. exact-head repository validation and CodeQL remained green through the acceptance-critical implementation slices.

Acceptance is a doctrine-maturity decision, not a claim that every deployment, storage family, or production implementation enforces ADR-022. Runtime claims remain evidence-scoped under the runtime-evidence program and architecture-family exploration.

Implementation initiative: [issue #68](https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/68).

## Doctrine

> **Memory scope is an authority boundary, not a retrieval filter.**

> **Same agent does not mean same memory scope.**

> **Shared memory is a governed isolation domain, not the absence of one.**

> **Crossing a memory boundary is a governed consequence and must remain reconstructable.**
