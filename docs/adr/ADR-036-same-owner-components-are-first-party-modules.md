# ADR-036: Same-Owner Components Are First-Party Modules, Not Attributed Providers

## Status

Accepted

Supersedes the reuse posture recorded for same-owner components in [`08-source-material-index.md`](../08-source-material-index.md). Refines, and does not weaken, the role mappings in [ADR-035](ADR-035-agent-memory-is-a-governed-cognitive-framework.md) and [`39-implementation-ownership-map.md`](../39-implementation-ownership-map.md).

## Context

Agent Memory owns its architectural contracts. [ADR-035](ADR-035-agent-memory-is-a-governed-cognitive-framework.md) names implementation candidates for several of them, and [`39-implementation-ownership-map.md`](../39-implementation-ownership-map.md) records the ownership split: *"Reality Graphs | Agent Memory contract; CodeGenome candidate implementation"*.

Several of those candidates are owned by the same party that owns Agent Memory. `MythologIQ-Labs-LLC` owns CodeGenome, EvolveAI, GG-CORE/COREFORGE, and FailSafe, and Agent Memory itself.

The documentation nonetheless treats them with the caution owed to third-party sources. [`08-source-material-index.md`](../08-source-material-index.md) records for CodeGenome *"Independent synthesis preferred; copies/substantial portions retain required notice"* and for EvolveAI *"Independent synthesis preferred; direct reuse must satisfy applicable attribution/NOTICE obligations"*. Boundary tables list them alongside genuinely external providers, and the layer model refers to "either provider's internal ontology".

That framing has a cost beyond tidiness. It produced two concrete misreadings in practice:

1. **"X implements Y" read as "Y belongs to X."** A reader — including an automated one — encountering "CodeGenome is the initial first-party implementation of the Code Reality Graph" concluded the Code Reality Graph was external to Agent Memory and undecided, when the ownership map says the opposite.
2. **Reuse treated as constrained when it is not.** An MIT or Apache-2.0 grant is what a copyright holder extends to *others*. It does not bind the holder. Treating a same-owner repository as imposing attribution obligations on Agent Memory invents a restriction that does not exist, and then designs around it.

The owner has determined that same-owner components may be adopted wholesale, without restriction, and referenced within Agent Memory solely as Agent Memory modules.

## Decision

**A component owned by the same party as Agent Memory is a first-party module candidate, not an attributed provider.**

Concretely:

1. **Adoption is unrestricted.** Code, structure, and design from a same-owner component may be adopted wholesale into Agent Memory. No independent-synthesis preference, no notice obligation, no reuse ceremony applies between repositories with a common owner.

2. **Naming is Agent Memory's.** Once adopted, the work is named for the Agent Memory contract it implements, not for the component it came from. **CodeGenome-derived work in this repository is Agent Memory's Code Reality Graph (CRG) module.** EvolveAI-derived work is Agent Memory's Cognitive Metabolism module. No external attribution, provider label, or originating-repository name is required in the module, its API, or its documentation.

3. **The test is ownership, not licence.** A component qualifies when it shares Agent Memory's owner. Licence text is irrelevant to the question, because a licence constrains licensees and the owner is not one.

4. **Lineage remains recorded; attribution obligation does not.** [`40-aligned-projects-and-intellectual-lineage.md`](../40-aligned-projects-and-intellectual-lineage.md) and [`08-source-material-index.md`](../08-source-material-index.md) continue to record where ideas came from, because intellectual history has value. That is provenance, not a licensing duty, and it never requires the module to carry a provider name.

### Scope

**Covered — determined by the owner:**

| Component | Agent Memory module it becomes |
|---|---|
| CodeGenome | **Code Reality Graph (CRG)** |
| EvolveAI | **Cognitive Metabolism** |

**Covered by the test, role not yet determined:** GG-CORE / COREFORGE and FailSafe / Arbiter share the owner and are therefore adoptable on the same terms. Their contract mappings remain contested in [`39-implementation-ownership-map.md`](../39-implementation-ownership-map.md), so no module naming follows automatically. Adoption is unrestricted; *what they become* is an open architectural question.

**Explicitly not covered.** This ADR changes nothing for genuinely third-party components. UOR Framework, Graphiti, Hindsight, and MemOS remain external, keep their reuse postures, keep their source-rights records, and continue to qualify through the component-qualification path with `authority_effect: none`.

## Consequences

**Positive.**

- The Code Reality Graph can be built as a named Agent Memory module in a modular structure, which is what the ownership map always implied.
- The two misreadings above become structurally hard: the README ownership section and [`43-substrate-inventory-and-maturity.md`](../43-substrate-inventory-and-maturity.md) state ownership and maturity as independent axes, and this ADR removes the reuse framing that made them look coupled.
- Qualification machinery is reserved for what it is for — establishing that an **external** component's capability behaves as contracted.

**Costs, accepted.**

- Adopted code loses its originating-repository identity in this tree. Lineage documents remain the place to recover it.
- Same-owner components no longer earn qualification artifacts here, so their maturity in this repository is expressed as ordinary module maturity rather than as `evidence_proven` against an external contract. That is the correct expression: qualifying your own module against your own contract measures nothing.
- If ownership of any covered component changes, its classification must be revisited. Ownership is the test, so a change of owner is a change of answer.

**Neutral.**

- `code_graph_qualification.py` normalizes CodeGenome **and Graphify**. Graphify is third-party, so provider-neutral handling remains correct there. The module keeps its shape for the external half.

## Related

- [ADR-035](ADR-035-agent-memory-is-a-governed-cognitive-framework.md) — role mappings and the contracts Agent Memory owns
- [`39-implementation-ownership-map.md`](../39-implementation-ownership-map.md) — contract owner versus implementation candidate
- [`43-substrate-inventory-and-maturity.md`](../43-substrate-inventory-and-maturity.md) — what exists, where, and at what maturity
- [`SOURCE_RIGHTS_POLICY.md`](../SOURCE_RIGHTS_POLICY.md) — reuse posture for genuinely external sources
