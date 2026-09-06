# ADR-033: Capabilities Are Independently Declared and Deterministically Composed

## Status

Accepted

## Context

Agent Memory is a governed memory fabric over heterogeneous memory technologies. Recent first-party inventory work demonstrated that EvolveAI and CodeGenome are both multi-capability subsystems: each spans several storage, representation, retrieval, structural, lifecycle, provenance, or evaluation functions at different maturity levels.

The earlier architectural shorthand of assigning one dominant module role to one component is therefore insufficient.

External comparison reinforces the same conclusion. Modern memory systems routinely combine vector, graph, temporal, lexical, multimodal, procedural, lifecycle, and context-assembly functions in one product, while individual capabilities mature at different rates.

Existing doctrine already establishes:

- ADR-020: probabilistic discovery does not create consequence authority;
- ADR-022: storage co-location does not erase memory isolation domains;
- ADR-028: the normative core remains implementation- and language-neutral;
- ADR-032: module/substrate shape may change without becoming canonical structural authority;
- RFC-001: Agent Memory is a governed mutable memory fabric;
- PRD-001: the runtime needs a configurable component/module registry and deterministic routing.

The missing doctrine is the relationship among **component identity, capability identity, maturity, overlap, and selection**.

## Decision

Agent Memory adopts a **capability-oriented composition model**.

> **Component identity and capability identity are orthogonal. Capabilities mature independently and are selected or composed deterministically.**

The architecture MUST support:

```text
one component -> many capabilities
one capability -> many candidate component implementations
```

No component is required to belong to one exclusive module category.

No component release/version automatically confers equal maturity on all capabilities it contains.

## Capability declaration

A configured component MUST expose enough versioned declaration to identify:

```text
component identity
component version / implementation reference
configuration/profile version
deployment + unavailable posture
dependency/license metadata where applicable
observability/evidence hooks
capabilities[]
```

Each capability declaration MUST independently identify at least:

```text
capability identity/version
maturity
maturity evidence/reference where applicable
canonical / historical / derived / learned-state posture
scope/isolation posture
read/write/candidate behavior
currentness/invalidation semantics
correction/supersession behavior
deletion/residue behavior
migration/rebuild behavior
failure/unavailable posture where material
structural-mutation requirements where material
```

The implementation may represent this information with schemas, code types, manifests, or another versioned contract. The semantic requirements are normative; one serialization format is not.

## Capability maturity

Agent Memory adopts the following minimum maturity vocabulary:

```text
declared
implemented
runtime_wired
evidence_proven
reference_qualified
```

### `declared`

The component documents/designs the capability. Runtime implementation is not established.

### `implemented`

Material implementation exists. Supported product/runtime reachability is not established.

### `runtime_wired`

The capability is reachable through a supported runtime/product path under the declared profile and limitations.

### `evidence_proven`

Reproducible evidence exercises the claimed behavior against an explicit fixture or acceptance contract.

### `reference_qualified`

The capability satisfies the applicable Agent Memory conformance profile at the claimed boundary.

A capability may carry limitations in addition to maturity. Maturity labels MUST NOT be used to hide material limitations such as mock embeddings, incomplete deletion propagation, or non-persistent governance state.

## Deterministic overlap resolution

Several configured components MAY expose the same capability.

Agent Memory MUST NOT select among overlapping implementations using hidden registration order, import order, timing, accidental discovery order, or an unrecorded model preference.

Configuration/routing MUST establish one of:

```text
preferred implementation
allowed implementation set + deterministic selection rule
explicit composition rule
explicit ambiguity failure
```

A routing fallback MUST NOT silently lower:

- required capability maturity;
- scope/isolation guarantees;
- canonical/derived posture;
- currentness semantics;
- deletion obligations;
- failure posture;
- governance/authority requirements.

If no compatible capability implementation exists, the operation fails explicitly at the capability-resolution boundary rather than degrading into guessed behavior.

## Routing is not authority

Capability routing determines **where/how a memory operation may be represented, retrieved, or processed**. It does not authorize the consequential memory operation itself.

```text
capability selection
  != PAMA authorization
  != recall admission
  != structural mutation authority
```

A learned/heuristic router MAY recommend candidate implementations. Consequences that affect durability, scope, lifecycle, canonical meaning, or authority remain governed by existing Agent Memory doctrine.

## Capability vocabulary

Capability names SHOULD describe observable memory functions rather than brands or physical stores.

The current research vocabulary is maintained in:

`docs/programs/memory-modules/capability-vocabulary.md`

Examples include distinct graph, vector, temporal, procedural, multimodal, lifecycle, and context-composition capabilities.

The vocabulary MAY evolve additively or through normal schema/type evolution. Capability-name changes that reinterpret existing declarations are governed structural changes under ADR-032.

## Canonical state remains explicit

Multi-capability composition MUST preserve explicit canonical-state ownership.

A graph projection, vector index, learned representation, remote memory service, skill catalog, or cache MUST NOT become canonical Agent Memory state merely because it is selected for a capability.

When several writable components participate in one operation, the configuration MUST preserve an unambiguous logical commit/currentness boundary or explicitly use a governed transaction/coordination profile. Dual authority is not an acceptable emergent property.

## Evidence and restart implications

For consequential operations, evidence SHOULD preserve the component/capability resolution that materially affected the result:

```text
required capability set
minimum maturity/posture
selected component + version
selected capability + version/maturity
configuration/profile identity
fallback/composition decision where relevant
resulting component consequence
```

If restart changes the compatible capability set, Agent Memory MUST either reproduce a compatible interpretation or fail explicitly. Restart is not permission to silently choose a weaker implementation.

## First-party implications

### EvolveAI

EvolveAI may advertise several capabilities at independently earned maturity, including temporal graph, vector retrieval, exact retrieval, lifecycle/decay, consolidation, negative memory, persistence, and related functions.

Its first-party status does not make all capabilities `reference_qualified`.

### CodeGenome

CodeGenome may advertise several code-domain capabilities at independently earned maturity, including graph state/query/traversal, structural reasoning, impact propagation, vector representation/similarity, provenance, freshness, MCP exposure, and evaluation.

Its code-domain ontology does not become the canonical Agent Memory graph ontology.

## External-system implications

Complete external memory systems may be integrated by exposing one or several capabilities through an adapter/profile.

The adapter MUST NOT flatten a third-party product's internal ontology into Agent Memory canonical semantics merely for convenience.

## Consequences

### Positive

- represents actual multi-capability memory systems without artificial product categories;
- allows capability-specific maturity and honest partial implementation claims;
- permits overlap without accidental precedence;
- makes fallback and incompatibility observable;
- preserves first-party and third-party neutrality;
- enables module replacement while protecting logical memory invariants;
- provides a stable basis for #287 and #290 implementation.

### Negative

- configuration is more explicit and therefore more verbose than a one-backend registry;
- component authors must maintain capability-level evidence rather than one product-level readiness flag;
- overlapping implementations require deliberate operator/default-profile policy;
- capability vocabulary requires versioning discipline.

These costs are preferable to hidden coupling and unverifiable product-level claims.

## Alternatives considered

### One exclusive module type per component

Rejected. EvolveAI, CodeGenome, MemOS, Hindsight, Cognee, and other systems demonstrate that real components routinely span several functions.

### One global maturity level per component

Rejected. Code can exist for one capability while another remains architecture-only or non-runtime-wired.

### First registered provider wins

Rejected. This makes runtime behavior depend on non-semantic ordering and can silently change after packaging/import changes.

### Let a model choose any available provider dynamically

Rejected as an authority-bearing default. Learned selection may recommend, but compatibility/maturity/scope floors and consequential routing must remain deterministically enforceable.

## Validation against current architecture

This ADR is consistent with and narrows, rather than replaces:

- ADR-020's proposal/authority separation;
- ADR-022's isolation-domain rules;
- ADR-028's implementation portability;
- ADR-030's compatibility/currentness requirement for derived consumers;
- ADR-032's mutable-substrate and structural-authority rules;
- RFC-001's governed mutable memory fabric;
- PRD-001's configurable runtime requirements.

No contradiction requiring supersession of existing accepted doctrine was identified in the #284/#286/#291 research pass.

## Implementation work

- #287: machine-readable capability maturity declarations;
- #290: deterministic capability-based routing and overlap resolution;
- #280: parent configurable component/capability registry;
- #292/#293: first-party capability qualification after the contract exists.
