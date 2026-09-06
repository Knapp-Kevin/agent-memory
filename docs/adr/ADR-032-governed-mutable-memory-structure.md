# ADR-032: Governed Mutable Memory Structure

## Status

Accepted

## Context

Agent Memory cannot assume that one fixed representation, domain ontology, storage substrate, or retrieval technology will remain appropriate for every deployment or every memory class.

Useful memory systems may discover new domain entities, relationships, derived representations, indexes, learned state, or storage needs after deployment. A rigid day-zero schema therefore creates a false choice between an architecture that cannot adapt and an architecture that silently lets uncertain inference rewrite durable semantics.

Existing doctrine already establishes several relevant boundaries:

- ADR-014 governs schema/type evolution;
- ADR-020 establishes that uncertainty may propose while authority constrains consequences;
- ADR-028 keeps the normative core language- and implementation-neutral;
- PAMA names `domain_schema_mutation` as a consequential operation;
- progressive domain-schema research separates Agent Memory doctrine schema, application/domain ontology, and derived projection shape.

The missing doctrine is the authority model for **structural adaptation itself**, including when Agent Memory may autonomously change memory shape and when the user must decide.

## Decision

Agent Memory adopts **governed structural mutability**.

> **Memory shape may adapt. Authority over canonical structural mutation may not be probabilistic.**

Learned, heuristic, probabilistic, or stochastic components MAY discover structural pressure, generate candidate schemas, propose migrations, estimate utility, rank alternatives, and predict impact.

They MUST NOT by themselves commit a change to canonical memory semantics, authority-bearing structure, isolation boundaries, lifecycle meaning, or destructive schema retirement.

A committed structural change requires either:

1. a deterministic, versioned governance rule that proves the change falls inside an explicitly authorized autonomous envelope; or
2. an explicit authorized human decision when the change exceeds that envelope.

This is a domain-specific strengthening of ADR-020. ADR-020 does not require every governance mechanism to be computationally deterministic. ADR-032 does require that **the authority determination which commits canonical structural mutation is deterministic or explicitly human-authorized**. Probabilistic evidence may inform that determination but may not be the deciding authority.

## Three structural layers

Agent Memory MUST distinguish at least these layers:

```text
canonical semantic shape
  what retained state means and which invariants govern it

application / domain ontology
  domain-specific entity, relation, field, and constraint structure

derived / physical representation
  indexes, embeddings, graph projections, caches, learned representations,
  storage layout, and replaceable substrate-specific structures
```

A change in a lower layer MUST NOT silently reinterpret a higher layer.

Derived representation changes may be rebuilt or replaced without becoming canonical semantic mutations when meaning, authority, provenance, scope, lifecycle, and currentness remain unchanged.

## Structural consequence classes

The governance classifier MUST evaluate structural changes by semantic impact, blast radius, reversibility, migration requirement, scope, authority effect, and dependency impact.

### Class S0: derived/rebuild-only

Examples:

- rebuild a vector index;
- change a cache layout;
- regenerate an embedding projection;
- replace a graph materialization while preserving canonical meaning.

These MAY be autonomous under deterministic maintenance policy.

### Class S1: bounded additive extension

Examples:

- add an optional project-local relation type;
- add a new derived attribute without invalidating existing records;
- introduce a reversible local representation that requires no reinterpretive migration.

These MAY be autonomous only when deterministic policy proves all configured conditions, including bounded scope, no authority widening, no destructive migration, explicit rollback, and preserved historical interpretation.

### Class S2: semantic or migration-bearing change

Examples:

- change field meaning;
- merge or split canonical/domain types;
- alter cardinality or interpretation of existing relationships;
- migrate existing durable memories into a new semantic model.

These require a user-visible proposal and authorized human decision unless a future accepted doctrine explicitly defines a narrower deterministic delegation profile for the exact change class.

### Class S3: destructive, cross-scope, or authority-bearing change

Examples:

- remove canonical structure still referenced by live state;
- widen project memory into tenant- or organization-wide scope;
- change isolation semantics;
- create permission-bearing or governance-bearing meaning;
- irreversibly destroy historical interpretability or evidence.

These require explicit authorized human decision and MUST NOT be autonomously committed by a probabilistic or merely confidence-scored process.

## Schema has lifecycle

Once durable state depends on a structure, removing that structure is itself a governed lifecycle event.

Structural evolution SHOULD follow:

```text
current schema/version
  -> proposed successor
  -> semantic diff + compatibility analysis
  -> dependency + migration + residue analysis
  -> governance decision
  -> successor activated for bounded writes
  -> migration / projection rebuild
  -> validation
  -> old version superseded
  -> retirement only after live dependencies and residue are resolved
```

Schema identity, version, provenance, compatibility, migration lineage, current/superseded state, rollback evidence, and dependency state SHOULD remain reconstructable.

The architecture prefers **supersession before retirement** over destructive replacement when historical interpretation or rollback matters.

## Module and substrate independence

Storage, retrieval, representation, and reasoning modules MAY impose different physical structures. Their implementation choices do not become Agent Memory doctrine merely because a deployment uses them.

First-party modules such as EvolveAI or CodeGenome and third-party/external modules are governed by the same rule:

```text
module capability
!= structural authority
```

A module may propose a structural adaptation needed for its operation. Agent Memory decides whether the adaptation is derived-only, autonomously permitted, review-required, or prohibited.

## Human decision quality

A human approval request for a structural mutation SHOULD present enough deterministic impact analysis to make the decision meaningful, including where available:

- exact current and proposed schema/version identities;
- semantic diff;
- affected memory count and scope;
- dependent modules/projections/consumers;
- migration requirement and expected information loss;
- authority or isolation effect;
- reversibility and rollback boundary;
- residue/rebuild requirements;
- source and estimator evidence for why the change was proposed.

The user should decide large semantic changes with recommendations, not with unexplained raw model output.

## Relationship to PAMA 1.2 and 1.3

PAMA 1.2 conservatively maps all `domain_schema_mutation` risk levels to review or external verification. That historical behavior remains valid and intentionally stricter than the autonomous envelope permitted by this ADR.

PAMA 1.3 provides the first executable structural-delegation profile without rewriting 1.2 semantics. It binds a `domain_schema_mutation` decision to an exact, versioned structural-impact record, deterministic classifier/policy identity, and current state/dependency digests.

The first delegated profile is deliberately narrow:

- S0 is classified but remains unchanged-semantic derived maintenance rather than `domain_schema_mutation`;
- a deterministically eligible S1 may resolve to `allow_with_ledger` with deterministic selection;
- S2 remains human-review required by default;
- S3 remains external-human or stricter and may be blocked by existing PAMA floors;
- state or dependency drift invalidates the prior structural authorization;
- estimator confidence, estimator disagreement, repetition, or prior autonomous success cannot lower the authority floor.

Historical 1.2 decisions remain valid. Consequential consumers that cannot interpret PAMA 1.3 must fail safely rather than treating the structural bindings as optional metadata.

Executable profile: [`../profiles/pama-1-3-structural-delegation.md`](../profiles/pama-1-3-structural-delegation.md).

## Consequences

### Positive

- permits Agent Memory to evolve without selecting a universal fixed schema;
- preserves user authority for sweeping or meaning-changing decisions;
- allows deterministic autonomous maintenance for low-impact structural work;
- keeps learned discovery useful without turning it into structural authority;
- supports module/substrate replacement without making backend shape canonical;
- gives schema retirement the same lifecycle discipline applied to memory content.

### Negative

- requires explicit structural classification and impact analysis;
- adds migration, dependency, rollback, and residue bookkeeping;
- may keep older schema versions alive longer than a destructive rewrite would;
- requires implementations to distinguish semantic change from derived representation maintenance.

## Rejected alternatives

### Fixed schema forever

Rejected because operational domains and useful memory representations evolve after deployment.

### Model-directed schema mutation

Rejected because probabilistic usefulness estimates are not sufficient authority to change durable semantics.

### Human approval for every structural change

Rejected because derived rebuilds and tightly bounded additive changes can be safely automated under deterministic policy.

### Treat every backend/index change as schema mutation

Rejected because physical and derived representation changes are not canonical semantic changes when higher-layer meaning remains intact.

## Implementation status and remaining follow-up

The first versioned structural-impact/classification record and bounded PAMA 1.3 S1 delegation are implemented under issue #281. The reference evidence covers deterministic S0-S3 classification, one narrow S1 autonomous path, S2 review, S3 blocking pressure, stale state/dependency invalidation, explicit rollback evidence, and supersession/retirement gates.

Remaining implementation work belongs to concrete module/runtime integrations rather than to this doctrine decision itself, including:

- bind module configuration to explicit structural capabilities and migration posture;
- exercise provider-specific migration/rebuild execution where a component claims it;
- ensure public architecture surfaces continue to distinguish Agent Memory semantics from configured module/substrate shape;
- add further structural delegation profiles only when evidence supports a distinct bounded class rather than broadening S1 by convenience.

## Doctrine

> **Agent Memory may change how memory is shaped, represented, and stored. Probabilistic systems may discover and propose those changes. Canonical structural consequences are committed only through deterministic authorized policy or explicit human authority, with authority escalating as semantic impact, scope, blast radius, migration cost, and irreversibility increase.**
