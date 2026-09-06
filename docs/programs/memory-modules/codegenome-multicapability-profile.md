# CodeGenome Multi-Capability Agent Memory Profile

Issue: #293

Status: **evidence-bounded first-party component profile**

## Exact source boundary

This profile is bound to:

```text
MythologIQ-Labs-LLC/CodeGenome@43a6b7147ec78ec5c616723fa1dd30f342174860
```

That revision includes the file-identity, traversal-direction, and cross-file semantic-resolution correctness repairs discovered during earlier Agent Memory qualification work.

CodeGenome is MIT-licensed at this pin. The profile records CodeGenome as a runtime-allowed first-party implementation, but first-party ownership does not grant capability maturity, Agent Memory authority, or canonical doctrine status.

## What this profile is

`reference/fixtures/component-capabilities/codegenome.example.json` is the machine-readable `component-capability-v2` declaration for the tested CodeGenome revision.

It intentionally separates:

```text
source implementation evidence
  != supported runtime reachability
  != executable qualification
  != reference qualification
```

A CodeGenome capability may therefore be present in source while remaining only `implemented` in Agent Memory.

The current profile contains eighteen independent capability rows. Maturity does not propagate between them.

## Current earned maturity

| Capability | Current profile maturity | Enabled | Boundary |
|---|---|---:|---|
| content-addressed code identity | `implemented` | yes | Code-domain content identity; not Agent Memory logical identity. |
| multi-overlay graph state | `implemented` | yes | Provider-derived code reality; not canonical Agent Memory state. |
| code graph traversal | **`evidence_proven`** | yes | Bounded matched-runtime qualification exists. |
| graph candidate retrieval | `implemented` | yes | Not separately qualified from traversal. |
| graph-augmented context assembly | `declared` | **no** | Graph traversal does not prove GraphRAG/context assembly. |
| structural program analysis | `implemented` | yes | Domain evidence only. |
| impact propagation | `implemented` | yes | Proposal/evidence surface only; no mutation or action authority. |
| embedding persistence | `implemented` | yes | Source implementation exists; runtime qualification remains open. |
| vector similarity | `implemented` | yes | Similarity is ranking evidence, not recall permission. |
| vector candidate retrieval | `implemented` | yes | k-NN exists in source, but the supported product path has not been qualified. |
| confidence/evidence fusion | `implemented` | yes | Fused confidence is evidence, not truth or authority. |
| freshness/currentness | `implemented` | yes | Provider signals do not replace Agent Memory currentness. |
| provenance/observer separation | `implemented` | yes | Provider provenance remains provider evidence. |
| multi-language extraction | `implemented` | yes | CodeGenome IR remains domain state, not core Agent Memory schema. |
| MCP/agent exposure | `implemented` | yes | MCP exposure is not Agent Memory conformance or permission. |
| experiment/evaluation | `implemented` | yes | May propose changes; cannot promote its own capability or authority. |
| LSP overlay | `declared` | **no** | The pinned implementation is still a stub that contributes no graph edges. |
| deletion/rebuild | `implemented` | **no** | Disabled until Agent Memory-grade rebuild/residue evidence exists. |

There are currently no `reference_qualified` CodeGenome capabilities.

## Traversal qualification binding

The only capability above source-level maturity in this profile is:

```text
code_graph_traversal@1.0
  -> evidence_proven
```

Its evidence is owned by the provider-neutral qualification profile:

```text
code-graph-traversal-currentness@1.1.0
```

That exact runtime qualification uses:

```text
CodeGenome@43a6b7147ec78ec5c616723fa1dd30f342174860
Graphify v0.9.43@7281f27eac568f77f50910f59f84543458f5dfd1
```

The matched fixture proves requested file identity, upstream/downstream traversal fidelity, decoy isolation, full-rebuild currentness across source change, explicit provider-unavailable behavior, bounded deterministic fallback, raw provider evidence retention, and `authority_effect = none`.

It does **not** prove vector retrieval, GraphRAG, deletion completeness, LSP behavior, or every CodeGenome overlay. Those rows remain at their independently earned maturity.

Graphify is used as an Apache-2.0-compatible external comparator for the generic code-graph facts. It does not define Agent Memory ontology and is not declared the winner over CodeGenome.

## Scope posture

Every CodeGenome capability uses:

```text
scope_posture = external_scope_bridge
```

This is deliberate.

CodeGenome has repository/code-domain identity and scoping of its own. Agent Memory must explicitly bind that provider scope to the active Agent Memory tenant/project/isolation context before provider output can participate in governed recall or consequence selection.

The profile therefore refuses the stronger and misleading claim that CodeGenome natively `inherits_agent_memory_scope` or `enforces_agent_memory_scope`.

```text
provider repository scope
!= Agent Memory tenant/project scope
```

## Currentness, correction, and rebuild posture

Most source-level CodeGenome capabilities declare `provider_revalidated` currentness/correction/deletion behavior and `requires_requalification` for migration/rebuild changes.

That is intentionally conservative. It means Agent Memory does not infer lifecycle completeness from the mere existence of CodeGenome storage, status, freshness, or rebuild mechanisms.

The traversal qualification separately proves one bounded full-rebuild currentness scenario. It does not upgrade the generic `freshness_currentness` or `deletion_rebuild` rows.

Deletion/rebuild remains disabled because:

```text
provider rebuild/delete mechanism
!= Agent Memory deletion completeness
!= proof derived residue is gone
```

A future qualification must explicitly exercise correction, deletion, rebuild, residue, and scoped currentness before that row may be activated or promoted.

## Vector boundary

CodeGenome contains embedding persistence, cosine similarity, and k-nearest-neighbor implementation at the pinned revision.

Those facts establish source-level implementation only.

The current profile therefore keeps:

```text
embedding_persistence      = implemented
vector_similarity          = implemented
vector_candidate_retrieval = implemented
```

No vector row is `runtime_wired`, `evidence_proven`, or `reference_qualified` until an Agent Memory adapter invokes a supported CodeGenome product/runtime path, preserves raw evidence, binds model/representation identity, and passes currentness/scope/correction/deletion/failure pressure.

```text
embedding exists
!= vector retrieval is runtime-qualified
!= recall admission
```

## GraphRAG boundary

CodeGenome provides operational graph traversal and a substantial graph-derived structural context substrate.

That does not establish a separate end-to-end graph-augmented context assembly contract.

Accordingly:

```text
code_graph_traversal             = evidence_proven
graph_augmented_context_assembly = declared + disabled
```

This prevents the common product-taxonomy error where every graph-backed retrieval path is silently renamed GraphRAG.

## LSP boundary

The pinned CodeGenome README describes the LSP overlay as a stub that can detect `rust-analyzer` but contributes no graph edges.

The profile therefore requires:

```text
lsp_overlay.maturity = declared
lsp_overlay.enabled  = false
```

A future implementation may change that, but a newer CodeGenome commit does not inherit this profile or any prior qualification automatically.

## Confidence and evaluation are not authority

CodeGenome confidence fusion, impact propagation, and experiment/evaluation surfaces are useful evidence producers.

They do not mint Agent Memory truth, recall permission, structural authority, mutation authority, or action authority.

The only current `proposal_only` profile surfaces are:

```text
impact_propagation
experiment_evaluation
```

Everything else has `authority_effect = none`.

The profile validator rejects direct authority escalation.

## Fail-closed profile validator

`reference/agentmem_ref/crg/codegenome_profile.py` freezes the current evidence boundary.

It rejects, among other things:

- a CodeGenome source-version change without re-pinning;
- an unreviewed capability-inventory change;
- maturity above the per-capability evidence ceiling;
- vector candidate retrieval promoted beyond `implemented`;
- GraphRAG activation or promotion;
- LSP stub activation;
- deletion/rebuild activation without dedicated qualification;
- loss of the exact traversal qualification binding;
- provider scope being mislabeled as Agent Memory-native scope;
- canonical Agent Memory state claims;
- direct authority escalation;
- any `reference_qualified` claim at this profile revision.

The profile therefore fails closed instead of letting one successful component test become a permanent repository-wide halo.

## Exact-head evidence

The dedicated `CodeGenome Multi-Capability Profile` workflow:

1. validates the v2 declaration and adversarial maturity tests;
2. checks out the exact CodeGenome pin;
3. verifies its MIT license and exact source-evidence paths;
4. executes the cross-file resolver regression, CodeGenome substrate library tests, and CLI build;
5. emits an Agent Memory exact-head profile report;
6. verifies maturity counts and all fail-closed invariants;
7. uploads the report and exact CodeGenome license as evidence.

The heavy `Component Qualification Evidence` workflow remains the owner of the real CodeGenome/Graphify traversal qualification. The profile workflow does not duplicate that comparator or reinterpret its result as proof for unrelated capabilities.

## Promotion rule

A future CodeGenome capability promotion must be capability-specific and version-bound:

```text
exact CodeGenome revision
+ exact adapter version
+ exact qualification profile
+ exact runtime/dependency configuration
+ raw provider evidence
+ normalized Agent Memory evidence
+ relevant negative paths
    -> earned maturity for that capability only
```

A repository release, test count, model score, repeated successful run, or neighboring capability's maturity cannot substitute for that chain.

## Claim boundary

This profile establishes a truthful, machine-readable CodeGenome capability inventory at an exact revision and binds the already-proven graph-traversal result into it.

It does not claim that CodeGenome is production-ready, universally conformant, a canonical Agent Memory substrate, a universal code ontology, or reference-qualified across all capabilities.
