# Glossary

A compact reader-facing glossary. The canonical terminology lives in `docs/00-glossary.md`.

| Term | Working meaning |
|---|---|
| **Agentic memory** | Retained state that can alter future agent interpretation, reasoning, planning, tool use, action, or adaptation across a persistence boundary. |
| **Authority** | Permission to create a consequence. Not the same as confidence, trust, or relevance. |
| **Basis** | The canonical units a projection was built from, each recorded at the version that was read. What makes staleness computable instead of asserted. |
| **Candidate** | State being considered for stronger persistence or another governed transition. |
| **Canonical state** | State that can only be wrong on its own terms. Derived state can additionally be wrong by being out of date, which is the difference that defines the boundary. |
| **Certification** | Required confirmation that a transition or artifact met a defined evidence/authority bar. |
| **Consolidation** | Transforming retained experience into summarized, generalized, semantic, procedural, or model-like state. |
| **Decision receipt** | Reconstructable evidence describing a governed decision, permitted actions, selected action, policy/version context, and before/after state. |
| **Derived state** | Any non-canonical state created from memory. Splits into derived *memory units*, which are governed and carry derivation links, and *projections*, which are not. |
| **Epistemics** | The system's uncertain interpretation of evidence: relevance, trust, contradiction, sensitivity, utility, etc. |
| **Forgetting** | A family of governed operations including decay, suppression, pruning, archival, redaction, tombstoning, deletion, and specialized unlearning. |
| **Governance envelope** | The bounded set of consequences allowed under current policy, scope, authority, and state. |
| **Governed recall** | Retrieval followed by authorization/admission and safe context composition. |
| **Inherited memory** | State that persists beyond the originating agent/process and is intentionally passed to a successor. |
| **Lifecycle strength** | Degree of persistence/reinforcement associated with retained state. |
| **PAMA** | Proportional Adaptive Mutation Authority, native Agent Memory doctrine for scaling authority to mutation consequence. |
| **Permitted action set** | Finite set of actions a selector may choose from after governance constraints are applied. |
| **Projection** | Derived state that is not a memory unit: an index, embedding, cache, materialized view, or clustered summary. Has no identity, lifecycle, or authority of its own, which is why deletion residue collects there. |
| **Provenance** | Evidence of origin, derivation, witnesses, scope, and transformation history. |
| **Recall admission** | Decision that a candidate memory may actually enter active context. |
| **Rebuild** | Recomputing a projection from its sources. Reproducible for deterministic transforms; for model-mediated transforms it commits new content and is therefore a governed mutation, not maintenance. |
| **Residue** | Content that survives a deletion. Acceptable when declared in the deletion receipt, disqualifying when undeclared. |
| **Saturation** | Persistence/lifecycle pressure derived from repeated or reinforcing state. It is not truth. |
| **Scope** | Boundary in which memory is valid, visible, or usable. |
| **Source trust** | Scoped evidence about expected source reliability. It is not authority. |
| **Stale** | A projection whose basis has changed since it was built. A relationship between projection and current state, not a flag on the projection — flags require something to reliably set them, and substrates reliably do not. |
| **Tombstone** | Durable record that a memory has been removed or invalidated while preserving enough history to prevent silent resurrection. |

## Canonical glossary

https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/00-glossary.md

## Related pages

- **[Core Concepts](Core-Concepts)**
- **[PAMA](PAMA)**
- **[Governed Uncertainty](Governed-Uncertainty)**
- **[Canonical and Derived State](Canonical-and-Derived-State)**
