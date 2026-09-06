# Component Adapter and Capability Qualification Contract

Status: **Research conclusion / implementation input**

Tracks: #298, #280, #292, #293

Evidence boundary: `MythologIQ-Labs-LLC/agent-memory@773ab1fac8b657e03522677f20740a1d816edf34`

## Why this contract exists

PR #297 proved two important pieces of ADR-033:

```text
component declaration
  -> independent capability maturity/posture
  -> deterministic provider resolution
  -> explicit ambiguity/maturity refusal
```

Those pieces answer **what a deployment claims is available** and **which configured provider may satisfy a capability requirement**.

They do not yet answer a different question:

> What exact behavior did a real component capability prove through a real adapter, against what version/configuration, and with what currentness, scope, correction, deletion, failure, and evidence properties?

That second question must be answered before `evidence_proven` or `reference_qualified` becomes more than a manually assigned label.

The stable next boundary is therefore:

```text
configuration / declaration
        !=
executable qualification evidence
```

## Architectural fit

No new ADR is required by the current evidence.

The contract specializes existing accepted doctrine:

- ADR-020: learned/probabilistic outputs may propose or rank but do not authorize consequences;
- ADR-022: component-native relevance does not bypass isolation domains or governed crossing;
- ADR-028: the core remains language/implementation neutral;
- ADR-030: serialized/derived output is not current merely because it can be consumed;
- ADR-032: component recommendations do not authorize canonical structural mutation;
- ADR-033: capabilities mature independently and compose deterministically;
- ADR-034: procedural/skill output remains retained influence rather than standing execution authority.

The missing surface is implementation/conformance machinery, not new doctrine.

## Three distinct surfaces

Agent Memory should distinguish three records that are easy to blur together.

### 1. Component installation/declaration profile

Answers:

```text
what component is configured
what capabilities it claims
what maturity/posture the deployment advertises
which provider may be selected
```

The existing `component-capability-profile` is the beginning of this surface.

### 2. Component adapter contract

Answers:

```text
how Agent Memory invokes a selected capability
how component-native output is preserved
how output is normalized without becoming canonical authority
how failure/currentness/scope/lifecycle signals are exposed
```

An adapter is transport/translation machinery. It is not a certification result and not a governance bypass.

### 3. Capability qualification record

Answers:

```text
what exact behavior was executed
against which exact implementation and adapter
under which qualification profile/configuration
which positive and negative cases passed
what maturity was actually earned
which limitations still apply
```

A qualification record is evidence, not installation configuration.

## Runtime flow

The smallest reusable runtime path is:

```text
Agent Memory capability requirement
  -> deterministic provider resolution
  -> versioned adapter invocation
  -> component-native result + raw evidence
  -> provider-neutral normalization
  -> Agent Memory currentness / scope / lifecycle evaluation
  -> PAMA or governed recall admission where applicable
  -> commit / admit / refuse
  -> evidence binding the whole path
```

The load-bearing separations are:

```text
selected component != authorized consequence
component result != canonical Agent Memory state
normalization != admission
component confidence != truth
component success != Agent Memory conformance
qualification != standing authority
```

## Adapter contract

The common adapter contract should be semantic rather than transport-specific. A component may be a library, CLI, MCP server, local process, sidecar, remote service, or another runtime shape.

A versioned adapter should expose or make reconstructable at least:

```text
adapter_id
adapter_version
component_id
component_version / exact implementation ref
capability_id
capability_version
operation / invocation kind
runtime/configuration identity
input reference(s) / digest(s)
component-native output reference(s)
raw evidence/artifact reference(s)
normalized candidate/consequence reference(s)
component currentness/freshness signal where available
component scope/partition signal where available
failure/unavailable result
trace/correlation reference
```

The common contract should not force every provider to emit identical native fields. The adapter preserves provider-native evidence and then produces the smallest Agent Memory normalization required for the requested capability.

## Provider-neutral normalized result

A normalized result should carry only semantics Agent Memory needs to continue its own governed path.

Depending on capability family, that may include:

- candidate references;
- exact identity/reference assertions;
- observed/inferred relationship claims;
- relevance/ranking evidence;
- proposed derived output;
- proposed maintenance/lifecycle consequence;
- source/currentness evidence;
- provider-native limitations;
- failure/unavailable posture.

It MUST preserve provenance back to raw provider output.

It MUST NOT silently translate:

```text
provider canonical
  -> Agent Memory canonical
provider confidence
  -> Agent Memory truth
provider PASS/BLOCK
  -> PAMA authority
provider graph reachability
  -> recall permission
provider success
  -> conformance
```

## Qualification applicability key

Qualification is version-scoped.

The minimum applicability identity should bind equivalents of:

```text
component_id
component implementation version / exact commit or release
capability_id
capability_version
adapter_id
adapter_version
qualification_profile_id
qualification_profile_version
runtime/dependency configuration identity
```

This means:

```text
qualified component v1
  != qualified component v2

qualified adapter v1
  != qualified adapter v2

qualified profile v1
  != qualified profile v2
```

A compatibility rule may explicitly carry evidence forward, but silence is not compatibility.

This rule does not require a new maturity vocabulary. It makes the existing maturity claim evidence-bounded and current rather than permanent.

## Qualification record

A qualification record should bind at least:

### Subject

- component repository/package/runtime identity;
- exact commit/release/package digest;
- component version;
- capability identity/version;
- adapter identity/version;
- qualification profile identity/version.

### Source-rights posture

- license identifier and source reference;
- material license exceptions/notices;
- whether runtime execution/adoption is permitted for the intended deployment;
- comparator-only restriction where applicable.

### Runtime identity

- dependency versions;
- model/embedder/parser versions where applicable;
- configuration/profile identity;
- deployment/local/remote posture;
- fixture/workload identity and digest.

### Positive capability evidence

- operations exercised;
- raw provider output refs;
- normalized output refs;
- expected behavioral facts;
- result and evidence digest.

### Negative/conformance evidence

As applicable:

- stale/currentness case;
- correction/supersession case;
- foreign-scope/isolation case;
- deletion/residue case;
- component removal/rebuild case;
- component unavailable/failure case;
- maturity shortfall case;
- ambiguous-provider case;
- confidence/relevance non-authority case;
- stale qualification/version-drift case.

### Result

- claimed maturity before execution;
- earned maturity after execution;
- limitations/blockers;
- evidence/artifact digests;
- exact qualification timestamp/build identity where useful;
- explicit non-claims.

## Maturity interpretation

The existing maturity vocabulary remains useful:

```text
declared
implemented
runtime_wired
evidence_proven
reference_qualified
```

This research adds an evidence rule:

### `declared`

Documentation/intended capability. No runtime proof required.

### `implemented`

Material implementation exists. Source evidence may establish this level.

### `runtime_wired`

A supported product/runtime path can invoke the capability. The path and version must be explicit.

### `evidence_proven`

A version-bound qualification record reproduces the claimed capability behavior against an explicit workload/fixture.

### `reference_qualified`

The capability additionally satisfies the applicable Agent Memory qualification/conformance profile, including the negative paths required for that capability family.

`reference_qualified` is not a repository-wide badge and does not automatically transfer to other capabilities or versions.

## Current gap against #280 / RFC-001

PR #297 earned:

- component/profile identity;
- capability identity/version;
- independent maturity;
- state/scope/failure posture;
- evidence refs and limitations;
- deterministic provider preference;
- allowed-provider filtering;
- maturity shortfall refusal;
- ambiguity refusal;
- no authority effect from routing.

Still missing for full #280:

- versioned adapter invocation;
- dependency/license metadata in the executable component contract;
- provider-native raw evidence preservation as a required runtime property;
- read/write/candidate operation semantics;
- currentness/invalidation contract;
- correction/supersession propagation;
- deletion/residue contract;
- migration/rebuild/removal behavior;
- capability-specific outage/failure evidence;
- version-bound qualification record;
- real two-provider portability evidence under one qualification profile.

## First portability proof: deterministic code graph

The first adapter qualification should intentionally avoid LLM/model variability.

### CodeGenome

Current tested first-party source boundary:

`MythologIQ-Labs-LLC/CodeGenome@d2578729a46d495369bd7613845002d50cf20f4c`

That revision includes the repairs discovered by #275:

- #8 / PR #9: file identity participates in target resolution;
- #10 / PR #11: requested impact direction controls traversal.

The qualification must retain those regression cases.

### Graphify

The old #275 comparator used:

`Graphify-Labs/graphify@7fe58b0b0f3873be9a21c30106b8b8527c353aa6`

That old pin remains historical evidence only.

For the new qualification, use a fresh released source pin. At the 2026-08-14 research boundary, upstream's latest GitHub release is `v0.9.43`; the tag resolves to commit:

`7281f27eac568f77f50910f59f84543458f5dfd1`

Graphify changed its active project license to Apache-2.0 in v0.9.25 while retaining pre-relicense MIT text in `LICENSE-MIT`/`NOTICE`. The code-only path is deterministic/local and its graph distinguishes `EXTRACTED` and `INFERRED` relationships.

The exact tag/license/package state must be revalidated when the comparator runs. Current research status is not a permanent dependency pin.

### Matched fixture

Harvest the adversarial structure from draft PR #278:

```text
main.rs
  leaf
  middle -> leaf
  top -> middle

decoy.rs
  middle -> decoy_leaf
```

The duplicate `middle` line range tests file-bound identity. Upstream/downstream queries test direction semantics.

The first qualification should add at least one update/currentness phase:

1. index v1;
2. prove expected edges;
3. change/remove a call;
4. update/rebuild through each supported provider path;
5. prove stale v1 structure is not reported as current;
6. preserve old raw evidence separately from the current result.

This turns the old comparator from a static correctness check into a first real adapter/currentness qualification.

## PR #278 disposition

Draft PR #278 is technically useful but architecturally stale.

Unique material:

- six small comparator/fixture/workflow files;
- real pinned CodeGenome CLI invocation;
- real pinned Graphify extraction;
- raw evidence preservation;
- neutral factual normalizer;
- no scalar product ranking.

Disposition:

```text
harvest design + fixture + factual checks
re-express against current main + #298 contract
close #278 as superseded
DO NOT merge its obsolete branch wholesale
```

## EvolveAI qualification consequence

EvolveAI remains a broad multi-capability candidate at:

`MythologIQ-Labs-LLC/EvolveAI@7cd42412ceed2ab638249a1517b2a6dac46f1312`

Open EvolveAI #19 currently blocks strong native deletion/audit claims: L3 `forget` removes the live vault entry without writing an explicit delete/tombstone event into the hash-chain ledger.

Therefore:

```text
live entry removed
  != reconstructable audited deletion
  != transitive forgetting completeness
```

Even after the native defect is fixed, Agent Memory still needs its own residue/dependency evidence before claiming semantic forgetting completeness.

## External memory-system pressure

The external frontier reinforces the adapter contract rather than requiring a new core ontology.

### Hindsight

Current release observed at this research boundary: `v0.9.1`.

Relevant shape:

- Retain / Recall / Reflect;
- world facts, experiences, mental models;
- semantic, BM25, graph, and temporal retrieval in parallel;
- bank/metadata isolation;
- current released packages/binaries suitable for a future real adapter test.

### MemOS

Current release observed: `v2.0.30` at source commit `f4db521214c29337164ec788bafede7eab236c25`.

Its local-plugin work exposes a useful metamemory/procedural pressure surface:

```text
L1 trace
L2 policy
L3 world model
Skill
Reflect2Evolve
```

That belongs behind ADR-034/ADR-032 boundaries, not as a reason to grant learned skill evolution configuration authority.

### Acontext

Apache-2.0 skill-memory layer using readable/editable skill files. Its file-centric shape is useful precisely because it differs from graph/vector systems while still needing the same identity/currentness/scope/correction/evidence contracts.

### MIRIX

From v0.1.6 onward, upstream describes MIRIX as a pure memory system API intended to plug into existing agents. It is a useful complete-memory-system adapter candidate rather than a canonical memory taxonomy.

### Memento-Skills

MIT-licensed deployment-time skill system with a `Read -> Execute -> Reflect -> Write` self-evolving loop. It is a strong adversarial comparator for ADR-034 because its native evolution loop must be decomposed into retained skill evidence, governed activation, and separately governed write/profile consequences when mapped into Agent Memory.

### EverOS / HyperMem

Apache-2.0 EverOS exposes runnable memory architectures and benchmarks; HyperMem provides a three-level topic/episode/fact hypergraph. This remains evidence for a high-order relationship capability family, not a reason to make hypergraph topology canonical Agent Memory ontology.

### GitNexus

GitNexus now exposes a rich local code-intelligence surface through MCP, skills, hooks, impact analysis, processes, and hybrid search.

Its current license remains PolyForm Noncommercial 1.0.0. For a commercial Agent Memory path it remains:

```text
source-level / behavioral comparator
!= runtime dependency
!= copied implementation source
```

unless separate commercial rights are obtained.

## Sequencing recommendation

The next implementation should be:

```text
#298 contract
  -> implementation slice: adapter + qualification record schema/harness
  -> CodeGenome + Graphify deterministic qualification
  -> #293 CodeGenome broader qualification
  -> EvolveAI #19 repair/re-pin
  -> #292 EvolveAI qualification against same harness
  -> general memory adapter proof (Hindsight/MemOS/Acontext/MIRIX candidate)
  -> #282 restart-safe multi-component acceptance
```

DashClaw #279 remains independently valuable for the Agent Governance peer seam and does not need to wait for every component qualification.

## ADR disposition

Current result:

`no_new_adr`

Reason:

The new findings fit accepted ADR-020, ADR-022, ADR-028, ADR-030, ADR-032, ADR-033, and ADR-034. The missing work is a reusable executable contract and evidence profile.

Reconsider an ADR only if real adapters expose a stable contradiction such as qualification authority or state ownership that existing doctrine cannot express.

## Acceptance signal for this research conclusion

This research layer is coherent when:

- #280 explicitly distinguishes completed selection work from missing adapter/qualification work;
- #292 and #293 use the same qualification gate;
- external source/license posture is refreshed;
- stale PR #278 is superseded rather than merged wholesale;
- RFC-001 and PRD-001 describe the same three-surface model;
- no current ADR claims are weakened or duplicated;
- the next implementation slice has a falsifiable two-provider workload.