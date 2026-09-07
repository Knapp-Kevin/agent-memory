# Decision Flows and Memory Lifecycle

This page is a **visual map of existing Agent Memory doctrine and explicitly scoped implementation evidence**. It is not a new doctrine source, decision table, runtime guarantee, or substitute for the canonical numbered documentation and ADR maturity process.

Use each diagram to answer one architectural question, then follow the canonical or evidence source link when implementation or conformance depends on the exact contract.

| Principal question | Visual | Canonical / evidence source |
|---|---|---|
| How can retained state strengthen, weaken, be disputed, corrected, reconciled, or pruned? | [Lifecycle state map](#1-memory-lifecycle-state-map) | [`docs/02-lifecycle-state-machine.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/02-lifecycle-state-machine.md) |
| Which signals strengthen or weaken persistence without creating authority? | [Strength and stability](#2-strength-and-stability-dynamics) | [`docs/03-scoring-and-decay.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/03-scoring-and-decay.md) |
| What authority outcome is allowed for a proposed mutation? | [PAMA decision flow](#3-pama-mutation-authority-decision-flow) | [`docs/pama/README.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/pama/README.md) |
| Which retrieved candidates may enter active context, and under what treatment? | [Governed recall](#4-governed-recall-pipeline) | [`docs/26-governed-recall-planner.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/26-governed-recall-planner.md) |
| How should readers distinguish supersession, correction, dispute, and staleness across time? | [Temporal change](#5-temporal-change-correction-and-supersession) | [`docs/18-temporal-causality-layer.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/18-temporal-causality-layer.md) |
| Why can a successful delete operation still leave memory behind? | [Deletion completeness](#6-deletion-completeness-and-derived-state-propagation) | [`docs/28-retention-deletion-and-tombstones.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/28-retention-deletion-and-tombstones.md) |
| What do these governance boundaries look like in executable cases? | [Scenario walkthroughs](#7-executable-scenario-walkthroughs) | [Conformance fixtures](https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/fixtures) |
| How can one physical store safely hold multiple project, task, and shared-memory boundaries? | [Isolation-domain crossing](#8-isolation-domain-crossing) | [`docs/41-memory-isolation-domains-and-governed-crossing.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/41-memory-isolation-domains-and-governed-crossing.md) |
| How can a memory decision be evidenced externally without exporting semantic authority? | [Portable evidence chain](#9-portable-governance-evidence-chain) | [P4.5 executable evidence](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/programs/runtime-evidence/portable-governance-evidence.md) |

## Reading rule

The diagrams deliberately preserve distinctions that are easy to destroy through visual simplification:

```text
confidence != truth
saturation != confidence
saturation != authority
relevance != permission
certification != permanence forever
staleness != falsity
supersession != correction
delete operation != forgetting completeness
retrieval != recall admission
same agent != same memory scope
proposal != commit
valid signature != permission
valid execution != authorization
valid DEL != forgetting
```

When a visual and a canonical document appear to differ, **the canonical document governs**. When an evidence-scoped visual and its executed evidence differ, the executed evidence governs and the diagram must be corrected. Open an issue rather than treating a picture as an independent policy or runtime claim.

## 1. Memory lifecycle state map

**Question:** How can retained state strengthen, weaken, be disputed, corrected, reconciled, or pruned?

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/lifecycle-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/lifecycle-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/lifecycle-flow-light.svg" alt="Agent Memory lifecycle state map showing strengthening and promotion, demotion, dispute, correction, reconciliation, pruning, and the separation between transition proposal and committed state" width="100%">
  </picture>
</p>

Not every memory traverses every state. `Crystallized` is durable under current evidence and policy, not eternal. `Pruned` removes memory from active recall or durable lifecycle consideration according to policy and does not necessarily mean physical deletion.

**Readable Wiki context:** [Lifecycle and Forgetting](Lifecycle-and-Forgetting)  
**Canonical contract:** [`docs/02-lifecycle-state-machine.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/02-lifecycle-state-machine.md)

## 2. Strength and stability dynamics

**Question:** Which signals strengthen or weaken a memory's case for persistence without creating authority?

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/strength-stability-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/strength-stability-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/strength-stability-flow-light.svg" alt="Agent Memory strength and stability map separating evidence confidence, source trust, saturation, contradiction pressure, certification, lifecycle stability, and PAMA authority" width="100%">
  </picture>
</p>

Evidence, verification, corroboration, meaningful reuse, and stable provenance can strengthen the case for persistence. Contradiction, expiry, invalidation, uncertainty, and drift can weaken it. Neither direction grants authority to promote, share, execute, or delete. Exact operating thresholds remain calibrated implementation choices rather than doctrine.

**Readable Wiki context:** [Core Concepts](Core-Concepts)  
**Canonical contracts:** [`docs/03-scoring-and-decay.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/03-scoring-and-decay.md) · [`docs/16-source-trust-and-reputation.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/16-source-trust-and-reputation.md) · [`docs/04-governance-and-pama.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/04-governance-and-pama.md)

## 3. PAMA mutation-authority decision flow

**Question:** What authority outcome is allowed for a proposed mutation?

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/pama-decision-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/pama-decision-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/pama-decision-flow-light.svg" alt="PAMA mutation authority decision flow showing proposal classification, authority floors, policy modifiers, outcome resolution, permitted action set construction, and commit or deferral with evidence" width="100%">
  </picture>
</p>

PAMA is multidimensional governance, not a single memory-quality score. Target class, lifecycle strength, requested operation, downstream authority, consequence, actor, evidence, uncertainty, and policy remain distinct. Confidence or saturation can contribute evidence but cannot expand an otherwise prohibited authority envelope.

**Readable Wiki context:** [PAMA](PAMA)  
**Canonical contracts:** [`docs/pama/README.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/pama/README.md) · [`docs/33-pama-decision-table.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/33-pama-decision-table.md) · [ADR-004](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-004-pama-controls-mutation-authority.md)

## 4. Governed recall pipeline

**Question:** Which retrieved candidates may enter active context, and under what treatment?

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/governed-recall-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/governed-recall-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/governed-recall-flow-light.svg" alt="Governed recall pipeline showing request resolution, candidate generation and normalization, recall admission, ranking only among admitted candidates, composition risk, context budgeting, governed assembly, and recall explanation" width="100%">
  </picture>
</p>

Candidate generation may be probabilistic. Admission is governed. Ranking occurs only among admitted candidates, composition has its own policy boundary, and context budgeting cannot discard required governance state. A stronger retrieval score never reopens a blocked candidate.

**Readable Wiki context:** [Implementation Guide](Implementation-Guide)  
**Canonical contract:** [`docs/26-governed-recall-planner.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/26-governed-recall-planner.md) · [ADR-013](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-013-governed-recall-planner-is-required.md)

## 5. Temporal change, correction, and supersession

**Question:** How should readers distinguish supersession, correction, dispute, and staleness across time?

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/temporal-correction-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/temporal-correction-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/temporal-correction-flow-light.svg" alt="Temporal change diagram distinguishing historically true state that is later superseded, wrong or incomplete state that is corrected, uncertain state that is disputed, and old but historically valid state that is stale for current-state recall" width="100%">
  </picture>
</p>

Supersession preserves a previously valid state while a newer state becomes current. Correction records that an earlier claim was wrong or materially incomplete within its claimed scope or time. Dispute preserves unresolved uncertainty. Staleness can reduce current-state usefulness without converting historical truth into falsity. Exact chronology does not establish causality, and inferred causal links must not rewrite the historical event log.

**Readable Wiki context:** [Lifecycle and Forgetting](Lifecycle-and-Forgetting)  
**Canonical contract:** [`docs/18-temporal-causality-layer.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/18-temporal-causality-layer.md) · [ADR-011](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-011-temporal-causality-is-required-for-memory-evolution.md)

## 6. Deletion completeness and derived-state propagation

**Question:** Why can a successful delete operation still leave memory behind?

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/deletion-propagation-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/deletion-propagation-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/deletion-propagation-flow-light.svg" alt="Deletion completeness diagram showing canonical memory, governed derived memory and projection state, correction staleness versus deletion residue, transitive purge, independent residue verification, and incomplete forgetting when undeclared residue survives" width="100%">
  </picture>
</p>

Canonical deletion doctrine requires propagation through known derivation relationships and verification of the requested forgetting outcome. The diagram's three-tier projection vocabulary, transitive-closure mechanics, and `stale`/`residual` relation come from **executed P4 design evidence that is not ADR-adopted doctrine**. That distinction is deliberate. The tested design makes the key failure mode legible without pretending its supporting ADR has matured: source change creates staleness; source purge can create residual content; and a row-level delete cannot prove forgetting completeness.

**Readable Wiki context:** [Lifecycle and Forgetting](Lifecycle-and-Forgetting) · [Canonical and Derived State](Canonical-and-Derived-State)  
**Canonical contract:** [`docs/28-retention-deletion-and-tombstones.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/28-retention-deletion-and-tombstones.md) · [`docs/31-recovery-rollback-and-replay.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/31-recovery-rollback-and-replay.md)  
**Executed design evidence:** [`docs/programs/runtime-evidence/canonical-and-derived-state.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/programs/runtime-evidence/canonical-and-derived-state.md)

## 7. Executable scenario walkthroughs

**Question:** What do these boundaries look like when the repository's fixtures exercise them?

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/scenario-walkthroughs-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/scenario-walkthroughs-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/scenario-walkthroughs-flow-light.svg" alt="Three governed-memory scenarios showing a supported memory entering pending verification rather than self-promoting, a highly confident false claim blocked from crystallization, and a raw deletion failing the forgetting outcome because derived residue survives" width="100%">
  </picture>
</p>

These are not hypothetical new policies. They are reader-oriented projections of existing conformance fixtures. [`governed-promotion-audit-trace.json`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/fixtures/governed-promotion-audit-trace.json) shows corroboration, cross-reference, reuse, proposal, authority resolution, a selected permitted action, committed `pending_verification`, and a reconstructable receipt. [`high-confidence-false-promotion.json`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/fixtures/high-confidence-false-promotion.json) demonstrates that confidence `0.99` and saturation `0.97` still do not permit crystallization of a false claim. [`deletion-residue.json`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/fixtures/deletion-residue.json) demonstrates that a deleted raw record plus surviving derived content forbids a full-deletion claim and requires continued dependency handling and verification.

The first scenario set is intentionally small and fixture-grounded. Cross-project isolation is now represented separately by the Accepted ADR-022 isolation-domain visual below rather than being retrofitted into these earlier walkthroughs.

## 8. Isolation-domain crossing

**Question:** How can one physical memory store host multiple project, task, and shared-memory domains without allowing memory to bleed between them?

> **Maturity: Accepted ADR-022 doctrine.** This visual explains the accepted isolation-domain boundary. It does not claim universal runtime enforcement or complete every broader #68 conformance path.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/isolation-domain-crossing.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/isolation-domain-crossing-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/isolation-domain-crossing-light.svg" alt="Agent Memory isolation-domain crossing diagram showing Project A Task 1, Project B Task 2, and a shared security space in one physical store; a cross-domain candidate must resolve current scope, membership, purpose, destination, and policy, pass PAMA governance, use only a permitted representation, and produce a reconstructable crossing receipt" width="100%">
  </picture>
</p>

The same physical store and the same agent do not collapse separate memory scopes. A highly relevant candidate from another project or task must still resolve the target domain and current authority before admission or transfer. Shared-space membership creates eligibility where applicable, not universal recall, mutation, export, or re-sharing authority. PAMA evaluates the crossing consequence, and only an allowed treatment may proceed. Permitted crossings remain reconstructable through a boundary-crossing receipt, while later correction, revocation, scope reduction, or deletion may create downstream propagation obligations.

**Readable Wiki context:** [Security and Privacy](Security-and-Privacy)  
**Canonical contract:** [`docs/41-memory-isolation-domains-and-governed-crossing.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/41-memory-isolation-domains-and-governed-crossing.md)  
**Accepted architectural decision:** [ADR-022](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-022-memory-isolation-domains-and-controlled-boundary-crossing.md)

## 9. Portable governance evidence chain

**Question:** How can a memory decision be evidenced externally without exporting semantic authority?

> **Maturity: executable evidence toward Proposed ADR-021.** This diagram is not an Accepted ADR visual and does not raise conformance.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/portable-evidence-chain-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/portable-evidence-chain-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/portable-evidence-chain-flow-light.svg" alt="Portable Agent Memory governance evidence chain showing the canonical decision receipt, a content-free signed evidence projection, correlation to runtime and Agent Manifest or TRACE-cMCP evidence, and separate verification of evidence integrity, governance disposition, runtime execution, and lifecycle satisfaction" width="100%">
  </picture>
</p>

P4.5 local implementation provides the executable shape issue #73 required before visualizing this boundary: a versioned content-free projection, deterministic canonicalization, Ed25519 issuer/verifier, Agent Manifest checkpoint correlation, TRACE/cMCP external-action correlation, lifecycle-result composition, and adversarial continuity vectors. The canonical Agent Memory receipt remains authoritative. Portable evidence proves integrity and correlation; it does not manufacture PAMA permission or lifecycle satisfaction. A valid negative outcome remains valid evidence.

**Readable Wiki context:** [Runtime Evidence](Runtime-Evidence)  
**Proposed architectural boundary:** [ADR-021](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-021-portable-memory-governance-evidence-boundary.md)  
**Executable evidence:** [`docs/programs/runtime-evidence/portable-governance-evidence.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/programs/runtime-evidence/portable-governance-evidence.md)

## Maturity boundary

The V1/V2 visual core, first executable scenario set, Accepted ADR-022 isolation-domain view, and evidence-scoped portable governance chain are represented.

[ADR-022](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-022-memory-isolation-domains-and-controlled-boundary-crossing.md) is **Accepted** doctrine. Its diagram therefore explains a canonical architectural boundary, while the broader implementation and conformance backlog in [#68](https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/68) remains separate and does not become complete merely because the doctrine is accepted or illustrated.

[ADR-021](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-021-portable-memory-governance-evidence-boundary.md) remains **Proposed** despite the executable P4.5 evidence above. Its visual remains explicitly evidence-scoped. A diagram does not raise an ADR status, conformance level, or runtime-evidence claim.

This page remains an index into stable or explicitly evidence-scoped visual explanations rather than an independent doctrine source.
