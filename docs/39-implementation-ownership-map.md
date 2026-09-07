# Implementation Ownership Map

## Purpose

[`05-repo-implementation-map.md`](05-repo-implementation-map.md) maps named implementation systems into Agent Memory roles and control classes. This document adds the ownership dimension: for each component of [`11-component-architecture.md`](11-component-architecture.md), who owns the doctrine, who is a candidate implementation owner, who consumes it, and what its implementation status actually is.

This distinction matters especially for PAMA: **Agent Memory owns the PAMA doctrine. A runtime implementation owner is still open.** Those are different facts and should not be collapsed into “no standalone PAMA repository exists.” No standalone external repository is required for native doctrine.

**Epistemic status for implementation ownership: declared, not verified unless stated otherwise.** This repository is the doctrine and conformance authority; it does not contain, build, or test most implementation systems named below. Every external ownership claim is a candidate assignment awaiting the implementation evidence defined in `05-repo-implementation-map.md`. Nothing here is a conformance claim unless it has the required evidence under [`35-interoperability-profiles.md`](35-interoperability-profiles.md).

## Status vocabulary

```text
doctrine-owned  canonical semantics are owned by Agent Memory
open            no verified runtime implementation owner yet
declared        implementation ownership asserted; no conformance evidence in this repo
partial         some implementation exists per its own repo's claims; unverified here
verified        implementation evidence linked and checked against doctrine
contested       more than one implementation claims primary ownership; consolidation needed
```

## Ownership map

| Component | Doctrine / primary owner | Secondary consumers or implementation candidates | Status |
|---|---|---|---|
| Identity Substrate | UOR Framework semantics as mapped by Agent Memory; CodeGenome for code-node identity | all components | declared |
| Evidence and Provenance | Agent Memory contracts | CodeGenome, FailSafe receipts, COREFORGE ledgers | declared, **contested implementation** — three ledger-shaped systems overlap |
| Reality Graphs | Agent Memory contract; CodeGenome candidate implementation | Runtime Memory | declared |
| Lifecycle Engine | Agent Memory lifecycle doctrine | EvolveAI proposer, COREFORGE Vault committer candidates | declared, **contested implementation** — the proposer/committer seam exists as code (see inspection record) |
| Saturation and Decay | Agent Memory scoring doctrine | EvolveAI implementation candidate | declared |
| **PAMA** | **Agent Memory native doctrine, authored by Kevin R. Knapp** | every mutating component; runtime policy module/service TBD | **doctrine-owned; runtime implementation open** |
| Certification | Agent Memory certification contract | FailSafe, Arbiter, approval workflows | declared, **contested implementation** |
| Runtime Memory Space | Agent Memory runtime contract | COREFORGE Vault / Neurospace | **partial** — implementation confirmed present by inspection; conformance unverified |
| Context Assembly | Agent Memory recall/context contract | COREFORGE and agent runtimes | **partial** — context broker/engine/packet confirmed present by inspection; conformance unverified |
| Correction and Dispute | Agent Memory correction/dispute contract | Vault and FailSafe-style workflows | declared, **contested implementation** |
| Durable Decision Memory | Agent Memory durable-decision profile | implementation candidates must map explicitly to profile | **doctrine-owned; runtime implementation open** |
| Conformance | this repository | every implementation | **verified** — schemas, fixtures, validators, CI |
| Failure / negative memory | Agent Memory negative-memory doctrine | Shadow Genome implementation candidate | declared |

## PAMA ownership

PAMA's canonical semantics live here:

- [`pama/README.md`](pama/README.md)
- [`04-governance-and-pama.md`](04-governance-and-pama.md)
- [`33-pama-decision-table.md`](33-pama-decision-table.md)
- [`adr/ADR-004-pama-controls-mutation-authority.md`](adr/ADR-004-pama-controls-mutation-authority.md)

The open implementation question is **where the authority evaluator and enforcement boundary run**, not who owns the framework.

A runtime implementation may live inside a larger repository or service if it preserves the semantic boundary. It must expose at least:

```text
M0-M5 target class
lifecycle strength
requested operation
A0-A5 downstream authority
actor and charter
scope and reversibility
evidence and uncertainty
policy version
permitted / prohibited outcomes
selected action
committed consequence receipt
```

PAMA must not be absorbed into a storage or estimator subsystem in a way that makes authority indistinguishable from relevance, confidence, saturation, or implementation convenience.

## Consolidation and segmentation calls

**Should consolidate** where implementations duplicate contracts:

- The three ledger-shaped implementation candidates (CodeGenome provenance, FailSafe receipts, COREFORGE ledgers) should converge on the decision-receipt and audit-event schemas ([`../schemas/decision-receipt.schema.json`](../schemas/decision-receipt.schema.json), [`../schemas/memory-audit-event.schema.json`](../schemas/memory-audit-event.schema.json)) rather than each defining a private evidence format.
- Lifecycle ownership must resolve to one committer: EvolveAI proposing transitions that Vault commits is a legitimate split (proposal versus commit per [`02-lifecycle-state-machine.md`](02-lifecycle-state-machine.md)); both committing is not.

**Should remain segmented** (per [`12-concept-segmentation-matrix.md`](12-concept-segmentation-matrix.md)):

- Certification must not collapse into the system that proposes candidates, whatever repo hosts both. Independence is the point.
- PAMA's authority boundary remains a separate, auditable module/contract regardless of which runtime repository implements it. The PAMA adapter of [`34-adapter-contracts.md`](34-adapter-contracts.md) is the seam.
- Identity stays out of every scoring system. No estimator gets to mint identity.
- Durable decision memory is an Agent Memory profile; an adjacent product does not become its doctrine owner merely because it implements decisions.

## External implementation inclusion rule

A named external or private implementation should appear in this map only when it adds specific value:

1. a concrete implementation responsibility;
2. evidence that can be mapped to an Agent Memory contract or profile;
3. a meaningful conformance candidate; or
4. a deliberate contested-ownership question that must be resolved.

Conceptual adjacency alone is insufficient.

## Inspection record

**2026-08-11.** Four candidate repositories were cloned and inspected directly, at pinned commits: EvolveAI `7c163f0`, CodeGenome `02565cc`, GG-CORE `f4ed6ca` (all public), and COREFORGE `48ee0ca` (private, default branch). Findings that bear on this map:

- **No doctrine backlink exists in any of the four.** Case-insensitive searches for `agent-memory`/`agent_memory` return zero doctrine references; COREFORGE's matches are local identifier names. Every graduation path in this document therefore still begins at its first step.
- **COREFORGE Vault/Neurospace exists as code**, not only as a claim: lifecycle store, mutation contract and gate with an approved/pending-review/vetoed envelope, Neurospace assembler/inspector/mutator, context broker/engine/packet, knowledge graph, UOR-style references, lineage, RAG engine. This moved Runtime Memory Space and Context Assembly to `partial`. Conformance remains unverified — existence of a mutation gate is not evidence that it enforces PAMA semantics.
- **The lifecycle proposer/committer split is a live seam**: EvolveAI and CodeGenome are consumed inside COREFORGE's Vault through in-tree memory-provider interfaces. The contested Lifecycle Engine row now has a concrete surface to resolve against.
- **GG-CORE holds no memory role and must not be recorded as the Vault successor.** Its architecture documents list `vault/` among forbidden modules, its `memory/` module is inference memory management (arenas, KV-cache, pools), and COREFORGE consumes it strictly as an optional compute dependency. Recorded here because the wrong successor narrative appeared once already and should not be re-derived.

Inspection verifies existence, never conformance. `partial` is the ceiling this kind of evidence can reach.

## Resolution path

Implementation claims graduate from `declared` only through the evidence items of `05-repo-implementation-map.md`: a doctrine backlink in the implementing repo, an implementation-alignment issue mapping its slice, and eventually fixture results claiming a profile from `35-interoperability-profiles.md`.

Contested rows are resolved by evidence and explicit cross-repo decision, recorded here with the decision reference, not by whichever implementation ships first.

Native doctrine ownership does not require that process. PAMA is already canonical doctrine; its runtime implementation remains subject to conformance evidence.

## Doctrine

Ownership is a governance fact, not merely a deployment fact.

A component's **doctrine owner** defines its obligations, contracts, conformance surface, and audit duties. An **implementation owner** must demonstrate that its code accepts those obligations.

Code without those obligations is not an owner. It is an unverified volunteer.
