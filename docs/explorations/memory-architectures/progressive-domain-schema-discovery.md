# Progressive Domain-Schema Discovery and Runtime Ontology Evolution

Status: **active exploratory research** under #226 and parent #67. This document is not canonical doctrine.

## Research question

Agent Memory already has accepted doctrine for **doctrine-level schema/type evolution** in ADR-014 and `docs/27-schema-registry-and-type-evolution.md`.

This study addresses a different problem:

> **How should an operational memory substrate discover and evolve its application/domain ontology at runtime without allowing the estimator that discovered the structure to acquire authority to make that structure durable or canonical?**

The distinction is mandatory:

```text
Agent Memory doctrine schema
!= application/domain ontology
!= derived index / projection shape
```

### Doctrine schema

Defines stable cross-implementation Agent Memory semantics such as lifecycle, provenance, scope, evidence, authority, receipts, and interoperability contracts.

Changes here remain governed by ADR-014 and normal doctrine/schema versioning.

### Domain ontology / domain schema

Defines application knowledge such as:

```text
Customer
 -> HAS_CONTRACT -> Contract
Contract
 -> HAS_RENEWAL_DATE -> Date
```

or domain-specific entity classes, relation types, fields, constraints, cardinalities, and extraction expectations.

A domain model can legitimately evolve while Agent Memory's doctrine schema remains unchanged.

### Derived index / projection shape

Includes implementation details such as embeddings, indexes, graph materializations, caches, topic clusters, and generated projection structures.

A rebuild or index-shape change is not automatically a domain-schema change if it does not reinterpret retained domain semantics.

## Comparator: Cognee custom graph models / Cascade

Current first-party Cognee documentation describes custom graph models as Pydantic `DataPoint` schemas that constrain which entities and relationships are extracted into a graph. Cognee's current Cascade material describes progressive schema discovery where a user can start from a smaller set of anchor entities/relationships and use reference data to expand/refine the custom graph model.

Primary sources:

- https://docs.cognee.ai/guides/custom-graph-model
- https://www.cognee.ai/blog/deep-dives/expanding-custom-graph-models-for-reliable-agent-memory-and-retrieval

Cognee is a comparator for the **capability**, not a dependency or authority source for Agent Memory semantics.

The useful challenge is real:

```text
complete domain model is not known on day zero
+
live data reveals useful new entity/relation structure
```

A governed memory system should be able to benefit from that discovery without choosing between two bad extremes:

```text
freeze ontology forever
or
let an LLM silently rewrite durable semantics
```

## Governed lifecycle

A representation-neutral lifecycle is:

```text
unexpected / domain-novel evidence
        -> domain-schema proposal
        -> source + estimator evidence
        -> semantic diff / compatibility analysis
        -> scope + migration + blast-radius analysis
        -> PAMA consequence envelope
        -> proposed | review | reject | authorized commit
        -> migration / projection invalidation or rebuild
        -> validation
        -> receipt
        -> currentness / rollback / supersession path
```

**Discovery is allowed to be probabilistic. Commitment is governed.**

## Proposal identity and evidence

A domain-schema proposal should preserve at least:

```text
proposal_id
current_domain_schema_ref
proposed_domain_schema_ref
proposal_kind
scope / tenant / project
source refs
independent source-root refs
estimator id/version/configuration
semantic diff
migration impact
projection impact
sensitivity / isolation impact
reversibility / rollback ref
policy/PAMA decision ref when committed
```

The estimator's confidence is evidence about its proposal. It is not authority.

## Mutation classes

### Additive local entity/relation/field

Example:

```text
new entity type: RenewalNotice
scope: one project
existing objects: unchanged
migration: none or additive
```

This is a **reusable operational model change**. It is more consequential than inserting one ordinary fact because it changes how future evidence may be structured and recalled.

Candidate PAMA dimensions:

```text
target: M3 reusable procedure/capability
influence: A3 local workflow mutation
risk: medium by default
reversibility: versioned/revocable
```

An estimator may generate the proposal automatically. Durable activation still requires the governed transition appropriate to the deployment policy.

### Semantic reinterpretation / type merge / type split

Examples:

- rename plus changed meaning;
- merge two previously distinct types;
- split one type and reclassify existing objects;
- change relation cardinality or semantics.

These can invalidate existing derived state and rewrite the interpretation of historical objects if handled carelessly.

Candidate dimensions:

```text
target: M4 when existing/shared semantic state is reinterpreted
influence: A3 or higher depending scope
risk: high by default
reversibility: versioned/revocable or unknown until migration proof
```

Historical objects and derivation evidence must not be silently rewritten merely to make the latest ontology convenient.

### Cross-scope / privileged semantic expansion

Examples:

- a project-local relation becomes tenant-wide;
- a discovered `Administrator` or `AuthorizedSigner` type gains permission-bearing meaning;
- a relation changes which principals may access shared memory.

These are not ordinary schema-maintenance operations. Existing PAMA scope/authority rules dominate:

```text
scope expansion / governance-bearing semantics
-> M5 / A5 where appropriate
-> explicit authority
-> no estimator self-approval
```

### Derived index change only

Examples:

- new vector index;
- different graph projection;
- re-embedding unchanged domain objects;
- topic clustering over the same canonical/domain semantics.

These are maintenance/projection operations, not domain ontology mutations unless they also change semantic interpretation. Autonomous maintenance is researched separately in #227.

## Current-contract audit

### Existing contracts that already apply

The current repository is already capable of expressing most governance requirements:

- estimator outputs are evidence, never authority;
- PAMA separates proposal from permitted consequence;
- provenance and root-source derivation can survive transformations;
- scope/isolation cannot be widened by representation changes;
- currentness can be re-evaluated after source revocation/deletion/supersession;
- schema migrations must preserve semantic/provenance evidence and rollback metadata;
- repeated/derived evidence cannot masquerade as independent corroboration;
- historical evidence need not be rewritten when current applicability changes.

### Concrete gap: PAMA operation vocabulary

The current canonical `pama-decision` operation enum includes generic `other`, but repository doctrine explicitly warns that `other` must not hide a **known consequential mutation class** merely to avoid schema evolution.

Progressive domain-schema mutation is now a known recurring class with distinct semantics:

```text
domain_schema_mutation
!= ordinary memory promotion
!= link creation
!= policy mutation
!= generic "other"
```

Using `promotion` understates that future extraction/interpretation rules are changing. Using `policy_mutation` incorrectly treats the application ontology as Agent Memory governance. Using `other` erases a now-known consequential class.

**Research finding:** the existing PAMA dimensions are sufficient to bound authority, but the canonical operation vocabulary lacks an exact domain-schema mutation class.

This is a narrow interoperability/receipt gap, not evidence that PAMA itself is insufficient.

No canonical enum change is made in this research slice. A separate implementation issue should evolve the closed operation vocabulary with normal schema-version compatibility and historical-receipt preservation.

## Representation-neutral adversarial scenarios

The executable research harness covers:

1. **Additive local type proposal**
   - estimator can propose;
   - proposal is not self-committed;
   - source/evidence lineage remains explicit.

2. **Privileged semantic proposal**
   - malicious input proposes an authority-bearing type;
   - estimator confidence cannot lower the authority floor.

3. **Cross-tenant relation widening**
   - domain similarity cannot erase isolation/scope boundaries;
   - existing scope-expansion PAMA path blocks the critical widening.

4. **Semantic merge based on similarity**
   - two fields/types that look similar cannot be merged without explicit semantic/migration review;
   - historical objects remain unchanged until an authorized migration exists.

5. **Repeated proposal self-corroboration**
   - replaying the same source/proposal does not create independent evidence.

6. **Source revocation after discovery**
   - a previously useful schema proposal/derived type becomes revalidation-required when its basis is revoked;
   - automatic rebuild cannot silently resurrect it as current.

7. **Projection residue after migration**
   - schema commit is not complete while stale embeddings/edges/projections still encode the old interpretation.

8. **Concurrent incompatible proposals**
   - conflicting ontology proposals are preserved as competing evidence;
   - last-writer-wins is not accepted as semantic reconciliation.

9. **Index-only maintenance**
   - changing a projection/index without changing domain meaning is classified separately rather than inflating every maintenance job into schema governance.

## Migration and currentness

An authorized domain-schema mutation may require:

```text
new schema version
+
explicit migration record
+
old-object compatibility state
+
derived projection invalidation/rebuild
+
post-migration validation
```

A migration must bind the source basis and what was reinterpreted. It must not destroy historical evidence in order to make the new model look retrospectively inevitable.

If later source changes invalidate the basis for the discovered type/relation:

```text
historical proposal/commit remains evidence
current applicability may become revalidation_required
future rebuild may not treat the stale proposal as fresh independent evidence
```

## Multi-agent convergence

Multiple agents may independently propose domain-model changes.

They should not resolve conflict by counting proposals or by last-write-wins. The relevant evidence is the independent source basis, semantic compatibility, scope, migration impact, and authority decision.

A useful model is:

```text
proposal A + evidence roots
proposal B + evidence roots
        -> compatibility/conflict analysis
        -> reconcile | preserve alternatives | review | reject
```

## Promotion recommendation

This research supports one narrow follow-on canonical change candidate:

> add an explicit `domain_schema_mutation` PAMA operation through the normal versioned operation-evolution process, with fixtures proving historical decisions remain valid and unknown-operation consumers fail safely.

No new domain-ontology schema is promoted to Agent Memory core. Substrates may use their own domain-model representations behind the common proposal/evidence/authority boundary.

## Non-claims

This slice does not establish:

- Agent Memory support for Cognee Cascade;
- Cognee runtime conformance;
- one universal ontology representation;
- automatic schema commitment;
- LLM-generated schema truth;
- universal migration safety;
- permission for a maintenance agent to self-authorize schema changes.

The comparator evidence establishes the architectural challenge. The executable research scenarios establish only the representation-neutral governance boundary tested here.
