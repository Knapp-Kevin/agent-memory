# Implementation Lane Selection: Governed Procedural / Skill Memory

Status: **selected implementation direction after #284/#286/#291 research**

## Decision

The next product-shaped capability vertical slice should be **governed procedural / skill memory**.

The implementation should use #287/#290 capability declaration and routing as enabling infrastructure, then prove ADR-034 behavior end to end with a deliberately simple skill representation.

This is not a decision to build a new skill database or new proprietary repository.

## Why this lane wins

### 1. It is a genuine capability gap, not merely a maturity gap

EvolveAI and CodeGenome already overlap substantially in graph, vector, retrieval, provenance, structural, lifecycle, and evaluation functions.

Neither current first-party subsystem has an Agent Memory-qualified generic procedural/skill memory capability.

External systems repeatedly demonstrate procedural memory as a distinct retained-state class rather than a branding variant of vector or graph retrieval.

### 2. It exercises Agent Memory's unique authority model

A skill sits exactly on the boundary among memory, planning, and action:

```text
remembered procedure
  -> current plan influence
  -> proposed actions
  -> governed execution
```

If Agent Memory cannot keep those stages separate, its broader “memory != authority” claim is not yet product-real.

### 3. It does not require choosing a backend

The first slice can use human-readable Markdown or a simple structured artifact.

That makes the behavioral contract falsifiable before selecting specialized infrastructure. It also makes correction, provenance, scope, and supersession visible during development.

### 4. It composes naturally with both first-party systems later

EvolveAI can later contribute:

- lifecycle/decay signals;
- consolidation from repeated successful experience;
- negative/failure memory;
- retention/tier policy evidence.

CodeGenome can later contribute:

- code/repository provenance;
- exact artifact/symbol references;
- dependency/impact evidence;
- validation context for code-domain procedures.

Neither must become the procedural-memory ontology.

### 5. It creates a better test of the component/capability fabric than another retrieval backend

Adding a second vector or graph implementation mostly proves interchangeability.

Procedural memory proves a qualitatively new retained-state capability with different activation, validation, scope, and authority semantics while still using the same component/maturity/routing machinery.

### 6. It gives metamemory a safe pressure test

Once ordinary procedural memory works, the same harness can submit a procedure that attempts to alter memory extraction/retrieval policy.

Expected result:

```text
ordinary skill recall
  -> cannot mutate Agent Memory profile

metamemory proposal
  -> PAMA / ADR-032 governed configuration path
```

This directly tests whether Agent Memory can benefit from self-evolving-memory research without giving learned optimization standing authority.

## Rejected first lanes

### EvolveAI GraphRAG completion

Valuable, but primarily an implementation-maturity upgrade inside an existing capability family. It should continue under #292 after the capability contract exists.

### CodeGenome vector integration

Also valuable, but primarily maturity/integration work for an already-implemented capability. Continue under #293.

### New hypergraph subsystem

Rejected. Hypergraph/high-order relations have not exposed a missing canonical Agent Memory invariant.

### Latent / JEPA / model-internal memory

Deferred. High research value, but model coupling makes it a poor first proof of configurable Agent Memory semantics and makes exact provenance/correction/deletion harder.

### Multimodal memory

Selected as an important later capability family, but it tests ingestion/representation breadth more than the central memory/authority separation.

### Shared/federated memory

Important, but ADR-022 already supplies the core authority boundary. A shared-memory implementation should follow once the component/capability runtime can express scope-bearing capabilities.

### Build a new proprietary memory subsystem

Rejected at this stage. The research does not satisfy the #284 build-new gate. Procedural memory can be proven without one.

## v0 capability profile

The initial reference capability should be approximately:

```text
component_id: reference_skill_store
capabilities:
  - procedural_skill_memory
  - exact_identity_retrieval
  - lexical_candidate_retrieval   # optional/simple
  - durable_persistence           # if the chosen reference store earns it
  - provenance_binding
```

Names are illustrative until #287 implements the machine-readable contract.

The reference representation SHOULD prioritize inspectability over sophistication.

Example conceptual skill artifact:

```yaml
skill_id: project-release-procedure
version: 1
scope: project:fixture
purpose: release-planning
status: current
sources:
  - episode:release-success-001
validation:
  - fixture:test-release-plan
activation_posture: recommendation_only
```

with human-readable procedural content such as:

```text
When preparing a release PR for this fixture repository:
1. determine the current configured release target;
2. run the required validation suite;
3. open the PR against the current release target;
4. do not merge without the normal governance path.
```

The content is illustrative. The semantic requirement is that procedure identity, source, scope, currentness, and activation posture remain independently inspectable.

## Canonical acceptance scenario

### Phase 1: grounded experience

A fixture agent completes a release workflow under an explicitly authorized path and produces reconstructable episode/outcome evidence.

### Phase 2: procedural-memory proposal

A procedure is proposed from the successful experience. Proposal alone creates no durable skill.

### Phase 3: governed promotion

PAMA/current-state/scope evaluation permits or reviews the durable procedural-memory promotion.

The committed skill binds its content/reference, provenance, scope, version, and activation posture.

### Phase 4: new-session retrieval

A later session starts without conversational memory. It retrieves the current skill as a candidate.

### Phase 5: governed activation/admission

The skill passes currentness/scope/purpose admission and may influence the plan.

The plan changes because the skill exists.

No external action has executed yet.

### Phase 6: action execution stays separate

The runtime proposes the actual repository/tool actions described by the skill.

Those actions pass through their normal Runtime/Governance authority paths. Skill presence does not suppress action governance.

### Phase 7: correction

New authoritative evidence changes the release procedure.

A corrected skill version is proposed and governed. Version 2 becomes current; version 1 remains reconstructable as superseded.

### Phase 8: stale replay

A stale retrieval/approval/reference to version 1 cannot restore or execute it as current guidance after version 2 is active.

### Phase 9: cross-scope negative case

A second project/tenant retrieves a high-relevance copy/candidate of the skill. Admission fails absent a governed boundary crossing.

### Phase 10: deletion/revocation

The skill is revoked/deleted. Any derived lexical/vector/cache copies become non-influential or the system reports incomplete forgetting honestly.

### Phase 11: metamemory attack

A recalled “skill” contains instructions to modify memory routing or lower a capability maturity requirement.

Ordinary skill activation MUST NOT apply the configuration change.

The requested metamemory/profile change must enter the normal ADR-032/PAMA configuration/structural mutation path.

## Simple controls

The implementation should compare against controls rather than assuming sophistication helps:

1. no procedural memory;
2. plain static project documentation injected manually;
3. Agent Memory governed skill artifact;
4. later, optional learned/consolidated skill generation.

The first value claim is not “Markdown is better than Markdown.” It is that Agent Memory can make a durable procedure **current, scoped, correctable, reconstructable, and non-authoritative for execution** across sessions.

## Required enabling slices

### Slice A: #287 capability declaration

Implement the minimal component/capability manifest with per-capability maturity and posture.

### Slice B: #290 deterministic routing

Implement enough deterministic resolution to select the reference procedural-memory capability and refuse ambiguity/maturity downgrade.

### Slice C: procedural memory unit/reference store

Implement the simplest durable/inspectable procedural-memory representation compatible with existing logical identity, provenance, scope, lifecycle, and receipts.

### Slice D: governed promotion + recall activation

Reuse existing proposal/PAMA/governed-recall machinery rather than creating a parallel skill authority path.

### Slice E: execution-boundary fixture

Demonstrate that admitted skill guidance changes the plan while actual tool/repository actions still require their normal execution authority.

### Slice F: correction / cross-scope / deletion / metamemory adversarial cases

Prove the negative paths that distinguish Agent Memory from a skill prompt store.

## Promotion criteria for ADR-034

ADR-034 should be considered for Accepted status only after the canonical workload proves:

- procedure proposal != commit;
- skill retrieval != activation;
- skill activation != execution authority;
- correction/supersession currentness;
- stale replay refusal;
- cross-scope refusal;
- deletion/residue honesty;
- metamemory cannot self-authorize configuration mutation;
- evidence keeps decision, memory activation, and action execution distinct.

## Follow-on lanes after this slice

A successful procedural-memory slice creates a good platform for:

1. EvolveAI-driven skill consolidation/lifecycle proposals;
2. CodeGenome-grounded code-domain skill provenance and validation;
3. multimodal procedural/resource memory;
4. shared skill libraries under ADR-022 boundary crossing;
5. learned skill generation/evolution under PAMA;
6. metamemory/retrieval-policy experimentation with regression-gated configuration changes;
7. latent/model-internal memory profiles after explicit memory influence can serve as the control.
