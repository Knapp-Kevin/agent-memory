# Memory Isolation Domains and Governed Boundary Crossing

> Canonical doctrine contract for [ADR-022](adr/ADR-022-memory-isolation-domains-and-controlled-boundary-crossing.md). ADR-022 is **Accepted** doctrine. Acceptance records doctrine maturity; it does not claim universal runtime enforcement, production conformance, or completion of every #68 follow-up.
>
> This contract extends [29-actor-scope-consent-and-tenancy.md](29-actor-scope-consent-and-tenancy.md) and does not supersede ADR-016.

## Purpose

Actor, tenant, project, repository, consent, delegation, purpose, and destination metadata are necessary governance inputs. They are not by themselves a proof that retained state stayed inside the memory boundary that authorized it.

This contract defines the logical boundary those dimensions resolve into: the **memory isolation domain**.

The core invariant is:

```text
physical_store != isolation_domain
same_agent != same_memory_scope
relevance != permission_to_cross
```

An isolation domain is a logical authority boundary over where retained state may exist, be discovered, be admitted into context, be combined, be transformed, and be transferred.

## Relationship to ADR-016

ADR-016 remains canonical and unchanged.

```text
ADR-016
  defines required scope, consent, delegation, tenancy,
  purpose, destination, and re-sharing dimensions

ADR-022 / this contract
  defines how those dimensions resolve into logical
  isolation domains and governed crossings
```

ADR-016 answers **which authority dimensions matter**. This contract answers **which memory boundary those dimensions authorize and what must happen when state crosses it**.

A deployment may satisfy ADR-016 metadata requirements and still fail this contract if it cannot distinguish same-agent project/task domains or reconstruct a crossing between them.

## Domain model

A memory isolation domain SHOULD have a stable identifier within the authority system that evaluates it.

A domain MAY be characterized by dimensions such as:

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

These dimensions do not form one universal hierarchy.

Valid deployments may use nested, intersecting, or orthogonal domains. For example:

```text
tenant/acme
  project/red
    task/security-review
  project/blue
    task/customer-analysis

shared/acme/security-findings
```

The same agent may participate in every domain above without receiving automatic authority to move memory among them.

### Required explicitness

The architecture does not require every deployment to populate every possible dimension.

It does require enough explicit state to answer consequential questions such as:

- what domain or domain set currently authorizes this memory?
- what domain is requesting recall or influence?
- is the actor a member of that domain under current policy?
- is the requested purpose compatible with the source constraints?
- does this operation stay inside the authorized boundary or cross it?
- if it crosses, which source and destination domains are involved?
- what authority permits the crossing?

Unknown or ambiguous domain state does not become broad permission.

```text
unknown_domain != global_scope
uncertain_membership != authorized_membership
```

For high-consequence use, policy must block, narrow, verify, or require review when the boundary cannot be resolved.

## Domain classes

The following descriptions are semantic roles, not mandatory schema enum values.

### Local or private domain

A domain whose membership and use are intentionally narrow, such as a user-private, agent-local, task-local, or project-local memory boundary.

Local does not mean physically local. A private domain may be stored in a shared service.

### Shared memory domain

A shared memory space is a broader governed isolation domain, not the absence of isolation.

Where applicable it should resolve:

- owner principal
- membership
- allowed readers and writers
- purpose
- admission policy
- sensitivity constraints
- correction and deletion authority
- re-sharing policy
- expiry and revocation behavior

Membership creates eligibility for governed use. It does not automatically grant recall admission, mutation, export, or re-sharing authority.

### External destination domain

A destination outside the current memory boundary, such as another service, trust system, agent, tenant, export target, or publication surface.

Serialization or API transfer does not make an external destination semantically neutral. Export is a governed consequence when the authority boundary changes.

## Domain membership

Membership is an authority fact evaluated under current policy, not a permanent property inferred from agent identity or prior access.

Membership MAY depend on:

- principal or actor identity
- role or capability
- tenant and organization
- project, repository, workspace, or task assignment
- purpose
- consent or delegation
- time or expiry
- revocation state
- shared-space policy

Prior membership does not imply current membership after revocation, task switch, project closure, role change, or delegation expiry.

## Task and project switching

Switching execution context does not imply memory scope migration.

When an agent moves from one task, project, workspace, session, purpose, or compartment to another:

1. the target context must resolve its own isolation domain or authorized domain set;
2. retained state from the prior context remains governed by its source domain;
3. prior-context memory must not remain influential merely because it is still present in a process cache, prompt, session buffer, or retrieval service;
4. any intended carry-over must be authorized as recall inside the target domain or as an explicit boundary crossing;
5. context assembly must remove or refuse state that no longer satisfies target-domain admission.

```text
same_process != same_context_authority
same_agent != permission_to_carry_memory_forward
```

A task switch that leaves prohibited prior-task memory in active context is an isolation failure even if no new database read occurs.

## Candidate visibility and recall

Governed recall must resolve the requesting context and target isolation domain before admission.

The architecture distinguishes:

```text
candidate_visibility
recall_permission
context_admission
derivation_permission
share_or_export_permission
downstream_action_influence
```

An implementation may combine capabilities only where policy proves them equivalent. They must not be assumed equivalent by default.

### Candidate generation boundary

Where candidate generation itself would expose prohibited content or metadata to an untrusted retriever, model, or caller, isolation must be enforced before candidate generation.

Where a trusted retrieval substrate may safely return cross-domain candidates for policy evaluation, discovery still grants no admission authority.

```text
semantic_relevance = 1.0
same_agent = true
wrong_project = true
=> context admission blocked
```

Ranking operates only after applicable domain and recall admission gates.

## Cross-domain writes and boundary crossing

A **boundary crossing** occurs when a consequential operation causes memory content, representation, authority, availability, or influence to move from a source domain into a destination domain not already authorized by the same boundary.

Candidate operations include:

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

The operation name alone does not determine consequence. A copy within the same authorized domain may not broaden scope; a summary sent to another project may.

A consequential crossing must be evaluated as governance, not as a retrieval or serialization side effect.

## Boundary-crossing decision record

A crossing decision or receipt should bind enough information to reconstruct the authority decision without requiring hidden reasoning.

Minimum semantic shape:

```text
operation
source_domain_ref
destination_domain_ref
actor
principal
purpose
representation
source_memory_or_derivation_refs
sensitivity
consent_ref / delegation_ref as applicable
requested_authority or consequence
PAMA disposition
policy_version
provenance
expiry / revocation state
outcome
timestamp
receipt_id
```

The repository now provides a machine-readable crossing representation through [`../schemas/boundary-crossing-receipt.schema.json`](../schemas/boundary-crossing-receipt.schema.json), together with isolation-domain state on the memory scope surface and executable reference behavior. This document remains authoritative for the semantic meaning of those fields and relationships; the schema does not redefine the doctrine.

A receipt proves what decision was made under bound policy/state. It does not make the crossing permanently valid after authority or domain state changes.

## PAMA integration

Scope crossing changes consequence and therefore participates in PAMA evaluation.

Where relevant, governance must consider:

- source domain
- destination domain
- audience or fan-out expansion
- purpose change
- sensitivity
- persistence
- reversibility
- shared or canonical status
- downstream authority
- representation form

Prior authorization inside the source domain cannot automatically relax the authority required for broader use.

```text
source_authorized != destination_authorized
read_authorized != export_authorized
high_confidence != scope_promotion_authority
```

## Derived-state scope propagation

A transform may change representation. It does not erase inherited authority or provenance obligations.

For derived state built from one or more sources, the default rule to validate is:

```text
derived_allowed_audience <= intersection(source_allowed_audiences)
derived_allowed_purpose  <= intersection(source_allowed_purposes)
derived_restrictions     >= union(source_restrictions)
```

This applies conceptually to governed derived memories and to projections such as:

- summaries
- embeddings
- indexes
- caches
- graph edges
- extracted entities
- materialized views
- synthesized memories

A representation that cannot carry full governance metadata must retain or bind enough provenance to recover the applicable source-domain constraints through an authoritative sidecar, manifest, derivation record, or equivalent governed mechanism.

Dropping scope metadata during transformation is not scope reduction. It is loss of governance state.

### Multi-source derivation

When sources have different domain constraints, the derived result does not silently inherit the broadest source.

The safe default is the compatible intersection of allowed audiences and purposes plus the union of restrictions.

If that intersection is empty or policy cannot resolve it, the derivation or subsequent admission must block, narrow, or require an explicit governed scope-promotion decision.

### Intentional broadening

Any intentional broadening beyond inherited constraints is a separate governed consequence.

```text
derivation != authority laundering
summary != permission to share
redaction != automatic export authorization
```

A policy may permit a narrower or privacy-minimized representation to cross where raw content cannot, but that permission must be explicit and receipted.

## Composition across domains

Individual admission does not prove that a combined context is safe.

Two memories may each be independently admissible while their composition violates:

- project or compartment separation
- purpose limitation
- aggregate sensitivity
- reconstruction constraints
- tenant separation
- contractual boundaries
- conflict-of-interest rules

Domain provenance must survive long enough for the composition-risk gate to evaluate the combined set.

A blocked composition must not be reopened merely because each component memory had a high retrieval score or valid individual read permission.

## Correction, dispute, revocation, scope reduction, and deletion

Authorized crossings create propagation obligations where policy requires them.

If memory crosses from domain A into B, later events may affect B and downstream derived state:

- correction
- dispute
- consent revocation
- delegation expiry
- membership revocation
- scope reduction
- deletion or purge

The propagation outcome may differ by representation and policy. For example, an independent private copy may not be silently mutated merely because a shared source was corrected, while a governed projection that claims derivation from that source may need to become stale or be rebuilt.

Deletion completeness remains distinct from a valid delete operation. If a crossing created governed or projected residue in another domain, forgetting is incomplete until the declared lifecycle obligation for that residue is satisfied.

## Domain lifecycle and closure

Domains themselves may have lifecycle events such as:

- creation
- membership change
- policy change
- purpose change
- merge or split
- closure
- archival
- revocation

Domain closure does not imply automatic deletion of every memory that was ever valid there.

Policy must determine whether retained state is archived, narrowed, transferred, tombstoned, purged, or retained for lawful/audit purposes. Any transfer to a successor or archival domain is itself evaluated as a crossing when the authority boundary changes.

## Inheritance

Inheritance between agents, tasks, projects, or generations does not automatically preserve authorization.

A successor receiving memory must evaluate:

- source domain
- destination domain
- acquisition mode
- current membership
- purpose
- consent/delegation status
- inherited restrictions
- expiry/revocation state

Inherited memory remains inherited evidence, not direct experience, and inheritance cannot silently broaden scope.

## Observability

Isolation evidence should distinguish events such as:

```text
domain_created
domain_membership_changed
cross_domain_recall_blocked
cross_domain_recall_admitted
scope_promotion_requested
scope_promotion_decided
memory_exported
memory_imported
shared_memory_admitted
shared_memory_revoked
derived_scope_recomputed
boundary_violation_detected
```

Telemetry must not leak prohibited content merely to prove that isolation worked. Event records should prefer identifiers, policy/state references, dispositions, and minimized metadata sufficient for reconstruction.

## Required negative paths

The schema and fixture work should make at least these failures expressible and testable:

- same agent, wrong project
- same agent, wrong task
- same tenant, prohibited compartment
- shared-store candidate from a non-member shared space
- task switch retains prohibited prior-task memory
- high-relevance cross-domain candidate
- allowed read but prohibited export or destination
- scope promotion without authority
- derived summary silently widens scope
- multi-source derivation incorrectly chooses the broadest scope
- individually allowed memories form a prohibited cross-domain composition
- scope reduction fails to propagate where required
- shared-memory revocation fails to affect subsequent admission

Critical isolation failures are hard governance failures. They must not be averaged away by good recall quality elsewhere.

## Machine-readable representation

The repository now has additive machine-readable support for the ADR-022 acceptance boundary, including:

- stable isolation-domain identifiers and domain-type/relationship state on the memory scope surface
- target isolation-domain, project, and task context for governed recall
- shared-space membership evaluation in the reference adapter
- source-domain provenance for derived scope
- a boundary-crossing receipt schema
- executable crossing decisions that bind source and destination domains, policy/PAMA state, and outcome
- revocation and destination constraints where the current reference paths exercise them

The representation remains deliberately non-hierarchical. It does not encode a universal tenant -> project -> task tree, and future schema evolution must preserve that property.

Machine-readable coverage sufficient for ADR acceptance is not the same as proof that every supported architecture family or production deployment enforces every isolation path.

## Shared-memory protocol relationship

The future multi-agent shared-memory protocol has been reconciled so that a shared space is explicitly modeled as a governed isolation domain.

Agent-to-agent sharing is therefore a controlled boundary crossing, not an exception that bypasses isolation doctrine. The protocol remains a future subsystem; reconciliation establishes semantic compatibility, not a claim that a production shared-memory implementation is complete.

## Conformance boundary

This canonical contract, together with the evidence recorded by ADR-022, supports **Accepted** doctrine status.

That acceptance does not by itself:

- raise a repository-wide conformance level
- prove universal runtime isolation across architecture families
- prove production deployment enforcement
- complete every broader #68 negative path or conformance fixture
- make membership sufficient for recall admission
- make a valid crossing receipt proof that later revocation, correction, scope reduction, or deletion obligations were satisfied

Those stronger claims require their own executable and runtime evidence.

## Canonical doctrine

> **Memory scope is an authority boundary, not a retrieval filter.**

> **Same agent does not mean same memory scope.**

> **Shared memory is a governed isolation domain, not the absence of one.**

> **Crossing a memory boundary is a governed consequence and must remain reconstructable.**
