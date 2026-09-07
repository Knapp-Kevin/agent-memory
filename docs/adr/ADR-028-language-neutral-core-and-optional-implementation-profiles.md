# ADR-028: Preserve a language-neutral core with optional implementation profiles

- **Status:** Accepted
- **Date:** 2026-08-12
- **Accepted:** 2026-08-13
- **Related:** #150, #232, ADR-021, ADR-020

## Context

Agent Memory is a reference architecture and research-driven doctrine for governed agent memory systems. Its normative value depends on remaining applicable across agent frameworks, languages, runtimes, storage systems, and trust substrates.

Issue #150 identifies potentially valuable prior art in the UOR ecosystem, including `uor-addr`, the UOR repository template, `kappa-registry`, and `uor-r4`. The proposal also suggests avoiding Python and rebasing the project on Rust-oriented UOR tooling.

The UOR work is relevant. In particular, `uor-addr` may provide useful deterministic content-addressing primitives; UOR repository governance patterns may inform conformance and evidence discipline; `kappa-registry` may be a useful implementation substrate for content-addressed storage, namespaces, graph relations, transactions, and integrity roots; and `uor-r4` may provide a useful witnessed inference substrate for conformance experiments.

However, adopting UOR or Rust wholesale would narrow Agent Memory from a portable reference architecture into an implementation-family architecture. That would create several risks:

- language choice could become confused with doctrine;
- Rust-specific repository machinery could become an accidental normative dependency;
- Python-first ecosystems, including Microsoft Agent Governance Toolkit integrations, could face unnecessary friction;
- other future implementations in JavaScript/TypeScript, Go, Java, .NET, or other runtimes could be treated as secondary even when they satisfy the same contracts;
- content identity could be conflated with logical memory identity, lifecycle identity, or governance authority;
- interoperability with one ecosystem could become architectural capture by that ecosystem.

The repository already reflects a more general boundary: `schemas/memory-unit.schema.json` permits a memory unit identifier to be a UOR address **or** another stable implementation-specific identifier. That flexibility should be preserved unless evidence demonstrates that a narrower rule is necessary.

## Decision

Agent Memory SHALL preserve a **language-neutral normative core**.

No implementation language, runtime, storage substrate, addressing scheme, external trust system, or third-party project SHALL become normative merely because the reference tooling or a high-quality implementation uses it.

The architecture distinguishes four layers:

```text
Normative doctrine / schemas / fixtures
        |
        v
Language-neutral conformance contracts
        |
        +--> Python reference tooling / integrations
        +--> Rust high-assurance implementations
        +--> JS/TS and other ecosystem implementations
        |
        v
Optional interoperability profiles
        +--> UOR
        +--> AGT
        +--> MCP
        +--> other trust/storage/runtime systems
```

### 1. Normative core

Normative Agent Memory doctrine, schemas, invariants, fixtures, evidence semantics, authority boundaries, lifecycle rules, and conformance requirements MUST remain expressible independently of a specific programming language or implementation substrate.

### 2. Reference tooling

Python MAY remain the primary reference-tooling language where it maximizes interoperability with agent frameworks, research tooling, evaluation systems, and ecosystems such as Microsoft Agent Governance Toolkit.

Reference tooling is evidence that the architecture can be implemented. It is not the definition of the architecture.

### 3. Rust implementations

Rust SHOULD be treated as a first-class implementation language, particularly for high-assurance components where memory safety, deterministic execution, canonicalization, cryptographic verification, low-level storage, performance, or `no_std` constraints materially matter.

Rust MUST NOT become the default normative language without separate evidence that such a constraint is required by the architecture rather than preferred by an implementation.

### 4. Optional interoperability profiles

External systems such as UOR SHOULD be integrated through explicit, bounded interoperability or implementation profiles.

A profile MAY define deterministic content-addressing rules, canonicalization requirements, mapping between external identifiers and Agent Memory references, storage or registry mappings, receipt/attestation/evidence projections, and cross-language conformance fixtures.

A profile MUST NOT silently redefine Agent Memory authority, lifecycle, correction, retention, deletion, or identity semantics.

### 5. Identity boundaries

Agent Memory MUST preserve the distinction between:

```text
logical memory identity
!= content identity
!= revision / governed-state identity
!= authority to mutate durable state
```

UOR-compatible addressing MAY be used for content or immutable revision references when appropriate. It MUST NOT automatically imply that the content hash is the logical identity of the memory unit or that possession/verification of an address grants mutation, recall, export, deletion, or overwrite authority.

## Consequences

### Positive

- Agent Memory remains portable across implementation ecosystems.
- Python integrations can remain frictionless where Python is the practical interoperability layer.
- Rust can be used aggressively where its properties create measurable assurance or performance value.
- UOR primitives can be reused without architectural capture.
- Cross-language conformance becomes a stronger proof of doctrine portability than any single implementation.
- The repository can evaluate additional substrates without repeatedly reopening the language-neutrality question.

### Negative / costs

- Maintaining language-neutral contracts requires discipline and may slow implementation-specific optimization.
- Multiple language bindings or conformance implementations increase test and maintenance surface.
- Optional profiles require explicit mapping documents and fixtures instead of simply inheriting a third-party architecture.
- Some useful UOR repository machinery may need adaptation rather than direct reuse.

## UOR-specific disposition

This ADR does not reject UOR. It fixes the integration boundary.

### Retain now

**`uor-addr` optional content-reference profile**

Issue #232 proves the pinned UOR-Addr v0.2.0 JSON realization across the released Python binding and released Rust crate while independently verifying annotated tag `4bdc4ec0...` and source commit `d78f82f...`.

The bounded profile may be evaluated for immutable evidence content references, receipt artifacts, immutable revision snapshots, derivation/output custody references, and lineage targets that denote content identity. Logical memory identity remains separate.

### Research separately before implementation

1. **UOR governance-pattern analysis**
   - compare claim registers, conformance IDs, BDD gates, and claim-honesty levels against Agent Memory evidence doctrine;
   - adopt only generally useful patterns without making Rust tooling normative.

2. **`kappa-registry` implementation profile**
   - evaluate content-addressed blobs, namespaces, graph edges, transactions, bundles, signed roots, filters, and garbage collection against Agent Memory contracts;
   - explicitly document authorization, privacy, distributed deployment, and lifecycle gaps.

3. **`uor-r4` conformance experiment**
   - evaluate witnessed inference artifacts as an optional evidence substrate;
   - do not import R4 inference architecture into Agent Memory doctrine.

### Do not pursue without new evidence

- rebasing Agent Memory onto the UOR repository template;
- replacing working Python tooling solely to standardize on Rust;
- making UOR addresses mandatory for all memory identifiers;
- treating UOR conformance as equivalent to Agent Memory conformance;
- making any third-party ecosystem authoritative for PAMA, lifecycle, correction, deletion, or memory mutation semantics.

## Acceptance evidence

ADR maturity criteria are satisfied by the bounded #232 implementation and its exact-head evidence:

1. the same seven JSON vectors execute through released Python `uor-addr==0.2.0` and released Rust `uor-addr=0.2.0` with zero cross-language mismatches;
2. the profile documents safe content-reference surfaces while keeping logical memory identity separate;
3. focused tests prove a valid content reference does not discharge existing PAMA review or repair an isolation-domain mismatch;
4. documentation distinguishes normative doctrine, reference tooling, implementation language, and optional interoperability profile;
5. UOR remains Apache-2.0-attributed, non-vendored, and absent from ordinary Agent Memory runtime dependencies;
6. no criterion requires rewriting Python tooling in Rust.

The inspected focused artifact at candidate head `a0bacc0d84d84f3a018f1d0ebd889bbf9cde0d05` records:

- 7 vectors;
- 0 cross-language mismatches;
- 0 canonical-equivalence failures;
- 0 typed-distinction failures;
- 0 failure-posture failures;
- all logical-identity/currentness/recall/scope/PAMA authority effects false;
- artifact digest `sha256:cd1b217491a24ad58972c995673417eb981d1f3cdc3e118ad15eb8b59e10bd0d`.

Because this ADR change itself advances the candidate head, merge still requires exact-head validation of the final head. The evidence above establishes the architectural decision; final-head CI establishes that the repository carrying the Accepted ADR remains conformant.

## Rejection or narrowing criteria

Revisit or narrow this decision if evidence demonstrates that:

- a language-neutral contract cannot express a required safety or conformance property without unacceptable ambiguity;
- a specific implementation substrate is necessary for a core invariant rather than merely useful for implementing it; or
- cross-language conformance repeatedly produces semantic divergence that cannot be resolved at the contract level.

Even in those cases, prefer the narrowest necessary implementation constraint over ecosystem-wide adoption.
