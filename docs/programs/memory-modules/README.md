# Memory Component Capability Program

Status: **program implementation complete; qualification remains capability- and version-scoped**

Program owner: #274

This program turns Agent Memory's representation-neutral doctrine into configurable component/capability contracts, deterministic composition, executable adapters, and version-bound qualification evidence.

## Core model

```text
component identity != capability identity

one component -> many capabilities
one capability -> many candidate implementations

configured capability != qualified capability
qualified old version != qualified new version
qualification evidence != authority
```

Capability roles such as graph, vector, GraphRAG, lifecycle, procedural memory, structural reasoning, storage, exact retrieval, multimodal memory, or learned representation are composable roles rather than exclusive product classes.

## Program outcome

The #274 implementation program has earned the reusable fabric it set out to prove:

- versioned component declarations and independent capability declarations;
- machine-readable capability maturity;
- per-capability state, scope, behavior, failure, evidence, and authority posture;
- deterministic overlap selection/composition or explicit ambiguity failure;
- minimum-maturity enforcement and downgrade-safe fallback;
- portable runtime configuration and deterministic validation;
- component enable/disable, removal, and rebuild behavior;
- hybrid composition that preserves component/capability/source boundaries;
- versioned provider adapters and common #298/#300 qualification records;
- raw-provider evidence retained alongside provider-neutral normalization;
- exact applicability binding across component, adapter, qualification profile, fixture, runtime/configuration, and evidence digests;
- explicit unavailable-provider evidence;
- first-party EvolveAI and CodeGenome profiles qualified capability-by-capability without first-party shortcuts;
- external alternatives mapped through the same capability vocabulary;
- source-rights/license posture recorded for material runtime/comparator evidence.

The program did **not** create a universal backend, a universal storage ontology, or a new logical-state algebra. #276's tested conclusion remains `no_new_algebra`.

## Current first-party qualification boundaries

### EvolveAI

Current qualified provider pin:

```text
MythologIQ-Labs-LLC/EvolveAI@21161ce7b88dbffeb7ed59757b4d02d24a9c2acd
```

That revision includes EvolveAI PR #21, which repaired EvolveAI #19 by recording explicit L3 delete history and reconciling live vault state against replayed store/update/delete history.

The current Agent Memory `component-capability-v2` profile contains 15 independent capability rows:

```text
1 declared
1 implemented
1 runtime_wired
8 evidence_proven
4 reference_qualified
```

The bounded `reference_qualified` set is:

- `content_addressed_exact_retrieval`;
- `persistent_snapshot_restart`;
- `audited_deletion`;
- `l3_provenance_audit`.

Important limits remain explicit:

```text
MockEngine runtime evidence
!= real GG-CORE embedding quality

graph + vector implementation
!= GraphRAG/context assembly

EvolveAI Shadow Verdict::Block
!= Agent Memory PASS/BLOCK authority

native audited L3 delete
!= transitive forgetting completeness
!= proof external derived residue is absent
```

Canonical evidence: [`evolveai-multicapability-profile.md`](evolveai-multicapability-profile.md).

### CodeGenome

Current qualified provider pin:

```text
MythologIQ-Labs-LLC/CodeGenome@43a6b7147ec78ec5c616723fa1dd30f342174860
```

The current Agent Memory profile contains 18 independent capability rows. The only capability above source-level maturity is:

```text
code_graph_traversal@1.0
  -> evidence_proven
```

No CodeGenome capability is currently `reference_qualified`. Vector retrieval, GraphRAG/context assembly, LSP, and deletion/rebuild remain bounded at lower maturity or disabled where executable evidence is incomplete.

Canonical evidence: [`codegenome-multicapability-profile.md`](codegenome-multicapability-profile.md).

## Common qualification boundary

The common qualification surface is:

- `schemas/component-capability-qualification.schema.json`;
- `reference/agentmem_ref/qualification.py`;
- [`component-adapter-qualification-contract.md`](component-adapter-qualification-contract.md);
- [`component-qualification-runtime.md`](component-qualification-runtime.md).

The required relationship is:

```text
selected capability implementation
  -> versioned adapter/result boundary
  -> raw provider evidence preserved
  -> provider-neutral factual normalization
  -> qualification-profile checks
  -> exact applicability digest
  -> earned capability maturity
```

The maturity vocabulary is:

```text
declared
implemented
runtime_wired
evidence_proven
reference_qualified
```

`reference_qualified` is a capability-specific, version-specific, adapter/profile-specific result. It is never a repository-wide badge.

## Deterministic routing and composition

The reusable routing fabric proves:

```text
required capability + minimum maturity + posture
        |
        v
eligible configured providers
        |
        +-- none -> explicit failure
        +-- ambiguous without policy -> explicit failure
        +-- configured preference/composition -> deterministic result
        |
        v
provider work / derived candidate
        |
        v
Agent Memory governance remains controlling
```

Selection cannot create mutation, recall-admission, structural, PASS/BLOCK, or action authority. Fallback cannot silently lower maturity or scope/isolation posture.

Runtime composition additionally proves component disable/removal/rebuild and hybrid composition without changing canonical logical identity merely because a derived provider is removed or replaced.

## Scope, currentness, correction, and deletion

Component capability evidence remains subordinate to Agent Memory's representation-neutral lifecycle boundaries:

- provider scope is explicitly bridged where it is not Agent Memory-native scope;
- stale or foreign-scope candidates fail closed;
- correction invalidates affected derived state according to declared behavior;
- provider-local delete does not imply transitive forgetting;
- rebuild and migration claims require exact evidence rather than inference from implementation existence;
- successful provider write is not lifecycle completeness;
- a provider's confidence, relevance, graph reachability, learned signal, or native verdict does not create Agent Memory permission.

## External frontier and build-vs-compose result

The external capability frontier is recorded in:

- [`external-capability-frontier.md`](external-capability-frontier.md);
- [`external-capability-frontier-refresh-2026-08-14.md`](external-capability-frontier-refresh-2026-08-14.md).

The completed #284/#286/#289 work found no evidence-based reason to create another proprietary memory subsystem merely to fill a taxonomy cell. EvolveAI and CodeGenome remain broad multi-capability systems; overlap is handled by capability-level composition and qualification.

The default decision order remains:

```text
retain inside EvolveAI or CodeGenome
-> compose existing components
-> move genuinely generic contract logic into Agent Memory core
-> adopt/wrap a suitable external implementation
-> build a new first-party subsystem only for a verified remaining gap
```

## Historical evidence is not rewritten

[`first-party-capability-inventory.md`](first-party-capability-inventory.md) remains intentionally pinned to its original August 14 source revisions. It records what the research knew at that evidence boundary, including EvolveAI #19 before repair and earlier CodeGenome pins.

The current qualification documents above supersede that inventory for **present capability maturity**, but do not rewrite the historical record.

Likewise, external frontier snapshots and qualification artifacts remain version-bound evidence rather than timeless product claims.

## Public configuration and installation surface

Agent Memory's primary product posture is attach-to-existing-stack. Configuration and installation guidance is documented in:

- [`../../CONFIGURATION.md`](../../CONFIGURATION.md);
- [`../runtime-evidence/runtime-configuration.md`](../runtime-evidence/runtime-configuration.md);
- [`../../../docs/prd/PRD-001-configurable-agent-memory-runtime.md`](../../../docs/prd/PRD-001-configurable-agent-memory-runtime.md).

The installed command boundary includes configuration validation, truthful doctor output, and read-only provider discovery/probing. Configuration does not silently mutate or replace an existing stack.

## Related completed work

- #274 — capability-oriented component program, closed after this synchronization passes exact-head validation;
- #275 — first-party/external adversarial comparison;
- #276 — logical-state algebra pressure test, `no_new_algebra`;
- #280 — configurable component/capability runtime and routing fabric;
- #284 — first-party capability inventory;
- #286 — external capability mapping;
- #287 — machine-readable maturity declarations;
- #289 — first-party subsystem boundary decision;
- #290 — deterministic overlap resolution;
- #291 — graph/vector/GraphRAG/hybrid vocabulary;
- #292 — EvolveAI multi-capability qualification;
- #293 — CodeGenome multi-capability qualification;
- #295 — governed procedural/skill memory vertical slice;
- #298 — adapter/qualification contract research;
- #300 — common executable qualification harness;
- #318 — attach-mode provider discovery and read-only probes.

## Program safeguards

```text
component != authority
capability != authority
declared capability != runtime capability
configured capability != qualified capability
provider success != Agent Memory conformance
retrieval score != recall permission
graph reachability != permission
first-party ownership != conformance
procedural memory != execution permission
old qualification != new-version qualification
matched capability result != universal product winner
provider-local delete != transitive forgetting
```

The closeout crosswalk is machine-readable in [`program-closeout.json`](program-closeout.json). Future capability work continues under bounded implementation/research issues and does not require #274 to remain permanently open.