# Actor Scope, Consent, and Tenancy

> Canonical requirement: [ADR-016](adr/ADR-016-actor-scope-consent-and-tenancy-are-required.md)

## Purpose

Memory authority is never universal by default.

A memory may be correct, useful, and safely stored while still being prohibited for another actor, tenant, project, purpose, destination, or agent.

This contract defines the scope metadata and governance rules needed to prevent usefulness from becoming accidental permission.

## Principals and actors

Distinguish where relevant:

- user/principal
- acting agent
- organization/tenant
- team
- project/repository
- tool/service
- destination agent
- external provider

An agent acts under delegated authority. Reading a memory does not grant the authority of the memory's creator.

## Scope dimensions

A memory may carry:

```text
owner_principal
origin_actor
allowed_readers
allowed_writers
tenant
organization
project
repository
purpose
sensitivity
consent_state
delegation_ref
allowed_destinations
reshare_policy
valid_from
valid_until
revocation_ref
```

Not every memory needs every field, but high-consequence shared memory should not depend on implicit ambient scope.

## Consent

Consent should identify what was authorized rather than one permanent boolean.

Useful dimensions:

- collection
- durable storage
- personalization
- external model use
- sharing with team/organization
- sharing with other agents
- export
- derived inference
- retention duration

Consent can be revoked or expire.

## Delegation

Delegated authority should be:

- scoped
- purpose-bound where applicable
- time-bounded where applicable
- revocable
- non-transitive by default unless policy says otherwise

Wrong:

```text
Agent A may read X
Agent B reads A's summary of X
therefore B inherits A's authority
```

Correct:

```text
every boundary evaluates the receiving actor's own authority
```

## Tenancy

Tenant identity is a hard boundary unless an explicit sharing policy authorizes crossing it.

```text
semantic_relevance = 1.0
wrong_tenant = true
=> recall blocked
```

Probabilistic retrieval may discover the candidate. It cannot authorize the crossing.

## Purpose limitation

A memory collected for one purpose may not be suitable for another.

Examples:

- support transcript used for immediate troubleshooting
- personal preference used for local personalization
- compliance evidence retained for audit

Using these for unrelated training, sharing, or profiling should require separate policy/authority as applicable.

## Scope promotion

Moving memory from narrower to broader scope is a governed transition:

```text
private -> team
team -> organization
organization -> public
local agent -> multi-agent shared memory
```

Scope promotion should record:

```text
requested_scope
current_scope
authority
consent/delegation
sensitivity
policy_version
selected_representation
receipt
```

## Scope reduction

Reducing scope may be necessary after:

- consent revocation
- role change
- project closure
- sensitivity reclassification
- security incident
- user correction

Derived and cached representations should follow the reduction where policy requires.

## Shared memory ownership

Shared memory should define who may:

- correct
- dispute
- supersede
- delete
- broaden scope
- narrow scope
- certify
- re-share

Ownership and authority are related but not identical. A system may own storage while a user retains authority over content use.

## Inherited memory

Successor agents should receive:

- origin
- acquisition mode
- scope
- authority constraints
- consent/delegation status
- policy version or migration state

Inherited memory is not direct experience, and inheritance does not automatically broaden scope.

## Uncertain identity or scope

Probabilistic entity resolution may be necessary when identity is incomplete.

For high-consequence disclosure:

```text
uncertain identity != permission
uncertain tenant != same tenant
```

Policy should block, narrow, or require verification.

## Conformance cases

### Cross-tenant perfect match

Expected: blocked before context admission.

### Expired delegation

Expected: prior access does not authorize current mutation or recall.

### Re-sharing

Expected: recipient cannot re-share unless policy grants that capability.

### Consent revocation

Expected: future governed use reflects revocation and required derived-state handling.

### Agent inheritance

Expected: successor sees acquisition mode and scope; does not claim direct observation or broader authority.

### Ambiguous identity

Expected: high-consequence sharing abstains or verifies rather than guessing identity.

## Decision receipt

For meaningful scope changes:

```text
memory_id
actor
principal
current_scope
requested_scope
consent_ref
delegation_ref
sensitivity
policy_version
outcome
before_scope
after_scope
timestamp
```

## Doctrine

Memory can be relevant without being yours.

Memory can be yours without being shareable.

Scope, consent, delegation, and tenancy determine which uses are actually authorized.
