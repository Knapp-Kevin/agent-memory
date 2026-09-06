# Runtime Evidence Program

## Purpose

Move Agent Memory from a **doctrine-validated** reference architecture to an **implementation-evidenced** one.

Everything in the doctrine tree is supported by internal coherence: schemas that validate, fixtures that are structurally sound, and ADRs that agree with the documents they govern. This program exists because coherence is necessary and still is not proof. It tests whether the architecture's boundaries survive real substrates, real workloads, adversarial cases, portability pressure, observability requirements, and cost.

> ADR-020 is Accepted on the executable evidence mapped by the P10 acceptance audit. That doctrine decision does not imply cumulative implementation conformance or universal production proof.

The completed runtime-evidence workstream is tracked in [issue #46](https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/46). This document is the durable in-repo statement of the program's rules, evidence surfaces, and completion boundary.

## Program completion posture

The runtime-evidence program owned by #46 is complete through its planned evidence slices:

- **P0** evidence floor: delivered under #43;
- **P2-P3** substrate mapping and governed reference adapter: delivered and exercised against the pinned real substrate;
- **P4** canonical/derived/projection correction, deletion, residue, and rebuild authority: delivered;
- **P4.5** portable governance evidence, Agent Manifest correlation, TRACE/cMCP action-evidence binding, and lifecycle composition: delivered;
- **P5** benchmark/security scorecard: delivered;
- **P6** pinned production-oriented Mem0 adversarial comparator: delivered;
- **P7** governed interchange: delivered through receiver-local authorization, lifecycle-obligation continuity, and two-store correction/deletion propagation;
- **P8** telemetry interoperability: delivered through strict minimization plus rotation-aware retention/deletion behavior;
- **P9** systems/economic characterization: delivered with structural cost/scaling measures and runner-specific non-gating timings;
- **P10** ADR-020 evidence acceptance audit: delivered, with ADR-020 accepted on the mapped evidence.

**P1 / #5 remains separate.** It tracks evidence-gated first-party implementation adoption/backlinks. P1 is a precondition before evidence from a first-party implementation is treated as dispositive; it is not unfinished reference-runtime or comparator work under #46. Closing #46 therefore does not close, satisfy, or weaken #5.

Likewise, broader isolation-domain conformance under #68, architecture-family exploration under #67, repository-governance hardening, and other future implementation/deployment evidence remain independent workstreams. Program completion means the planned #46 evidence program is complete, not that Agent Memory has exhausted every useful experiment or earned universal production conformance.

## What counts as runtime evidence

A claim becomes runtime evidence only when all of the following hold:

```text
executed        the path ran against a real substrate, not a diagram
pinned          substrate version, adapter version, policy version,
                estimator version, and fixture version are all recorded
reproducible    another operator can re-run it and get the same verdict
                (invariants, not identical stochastic outputs)
negative-tested the run includes paths that must fail, and they failed
reconstructable a receipt reconstructs estimate, authority, selection,
                and consequence after the fact
```

Evidence that omits the negative paths is a demo. Evidence that cannot be re-run is an anecdote. Both are welcome in a discussion and neither moves an ADR.

P4.5a is intentionally a **substrate-independent interoperability precondition** rather than a claim that another runtime substrate has been exercised. Its job is to make the portable evidence boundary executable and adversarially testable before correlation to Agent Manifest, TRACE, or another external runtime surface.

P4.5b is **external comparator evidence**: the tests execute the pinned Agent Manifest package's own checkpoint/delta verifier and correlate its verdict to Agent Memory receipts and portable evidence. Agent Memory does not copy the external checkpoint protocol or inherit its semantics.

P4.5c is **external action-evidence interoperability**: Agent Memory projects only content-free references into the existing TRACE/cMCP external execution-evidence path, keeps call identity distinct from Agent Memory action identity, and executes the resulting envelope through the released cMCP verifier. TRACE receipt validity remains separate from PAMA, runtime authorization, and lifecycle satisfaction.

The P4.5 lifecycle composition is **derived lifecycle evidence**: the actual P4 residue partition and independent sweep deterministically produce the public residual/zero-residue measurement, and that measurement drives the signed P4.5a `lifecycle_result`. The portable result is therefore downstream of the deletion-completeness evidence instead of being an adjacent assertion.

## Comparator discipline

External systems enter this program to answer one architectural question each, and are barred from becoming something else:

| Comparator | Its one job | Not allowed to become |
|---|---|---|
| Temporal graph substrate | first adapter target for time, provenance, and retrieval | doctrine authority |
| Production memory layer | adversarial comparator for accumulation, correction, deletion | replacement architecture |
| Lifecycle-contract and portability work | interoperability and interchange pressure | automatic standard |
| Governance and lifecycle-security benchmarks | access control, forgetting, Write to Execute to Forget stress | the sole quality metric |
| Task and long-horizon benchmarks | whether memory improves future action | a recall-only leaderboard |
| Telemetry conventions | observability interoperability | licence to emit memory content |
| Systems characterization | cost, latency, and scaling pressure | an authority signal |

Two standing rules follow from this table. A missing guarantee in an external system is a **classified gap**, not a bug, unless that system claims the guarantee. And a behavior observed in one product does not become Agent Memory doctrine without independent justification, otherwise the architecture is just the union of whatever shipped recently.

## Evidence rules for imported material

```text
portable        != trusted
imported        != admitted
interoperable   != authorized
benchmarked     != governed
```

Anything arriving from an external substrate, bundle, or benchmark enters normal Agent Memory evidence, scope, sensitivity, lifecycle, and authority handling on arrival. Adapters make decisions portable; they do not make them pre-approved.

## Scoring rule

No universal memory score. Program results are reported as the scorecard defined in [`../../32-memory-quality-metrics.md`](../../32-memory-quality-metrics.md): hard invariant gates first (disqualifying, un-averageable), then trap-class rates, then optimization and outcome metrics, with segment breakdowns. A benchmark aggregate that hides a cross-scope admission or a blocked-action escape is not a result, it is a press release.

## Layout

```text
docs/programs/runtime-evidence/     program material (this directory)
reference/                          executable adapters, policies, receipts, tests
```

Program material uses grouped paths rather than extending the canonical document numbering. Existing canonical document numbers are never reused.

Documents are added when their slice is ready to execute, not in advance. A directory of speculative placeholders would be its own small monument to unearned confidence.

| Document | Slice | Status |
|---|---|---|
| [`graphiti-conformance.md`](graphiti-conformance.md) | P2 first substrate capability mapping | documentation-verified, with key findings confirmed by execution |
| [`../../../reference/README.md`](../../../reference/README.md) | P3 minimal governed adapter | bound and executed against a real substrate |
| [`canonical-and-derived-state.md`](canonical-and-derived-state.md) | P4 canonical memory versus derived projections | design spike executed: all seven evidence-bar items run in CI |
| [`portable-governance-evidence.md`](portable-governance-evidence.md) | P4.5a portable governance evidence core | executable substrate-independent Ed25519 issuer/verifier and adversarial vectors |
| [`agent-manifest-correlation.md`](agent-manifest-correlation.md) | P4.5b Agent Manifest memory checkpoint correlation | pinned external comparator executed; a checkpoint built from a test log containing `DEL` remains distinct from Agent Memory lifecycle satisfaction |
| [`trace-action-evidence.md`](trace-action-evidence.md) | P4.5c TRACE/cMCP action-evidence binding | content-free action receipt adapter plus released cMCP verifier comparator; TRACE receipt state remains separate from Agent Memory governance and lifecycle |
| [`deletion-completeness-evidence.md`](deletion-completeness-evidence.md) | P4 -> P4.5 deletion lifecycle composition | declared residual, undeclared hard-gate failure, and zero-residue success drive signed portable lifecycle evidence and an exact-commit JSON report |
| [`concurrency-conflict-evidence.md`](concurrency-conflict-evidence.md) | concurrency behavior | conflicting proposals from one prior state are revalidated at commit; stale second write is deferred and conflict evidence is emitted |
| [`benchmark-security-scorecard.md`](benchmark-security-scorecard.md) | P5 benchmark/security matrix and harness | seven hard-gate security/governance metrics execute with explicit denominators and an exact-commit scorecard artifact; no scalar quality score |
| [`mem0-adversarial-comparator.md`](mem0-adversarial-comparator.md) | P6 production-oriented adversarial comparator | pinned Mem0 OSS memory CRUD, scope, correction, deletion, history, and direct-ID behavior execute against local Qdrant/SQLite with external-model seams removed |
| [`governed-interchange.md`](governed-interchange.md) | P7 governed interchange | receiver-local authorization, lifecycle-notice continuity, and two-store correction/deletion propagation execute without importing sender authority |
| [`telemetry-minimization.md`](telemetry-minimization.md) | P8 telemetry interoperability | strict content minimization plus expiry and rotation-aware targeted purge execute without turning telemetry into shadow memory |
| [`systems-economic-characterization.md`](systems-economic-characterization.md) | P9 systems/economic characterization | structural work and scaling measurements plus runner-specific non-gating timings are emitted as exact-head evidence |
| [`../../audits/governed-uncertainty/09-adr-020-runtime-evidence-acceptance-audit.md`](../../audits/governed-uncertainty/09-adr-020-runtime-evidence-acceptance-audit.md) | P10 ADR-020 evidence review | all fourteen ADR-020 minimum evidence gates mapped to executable repository evidence; acceptance separated from cumulative conformance |
| [`dashclaw-external-verdict.md`](dashclaw-external-verdict.md) | #279 DashClaw governance-adapter provider-side proof | executable v1 provider projection and governed release-branch workload; live cross-repository public-HTTPS integration remains required before #279 closes |

The DashClaw slice above is a later interoperability implementation product, not an additional phase of the already-completed #46 program.

## Preconditions

Before runtime evidence from a first-party implementation is treated as dispositive:

1. the repository evidence floor is closed (versioned fixtures, validated audit traces, quality gates, doctrine traceability);
2. doctrine-to-implementation identity is established for any implementation used as evidence, earned through a concrete responsibility or conformance surface rather than asserted;
3. the exact implementation, policy, estimator, fixture, and evidence bundle versions are reproducible.

External comparators do not require precondition 2. A comparator is measured, not adopted.

## Non-goals

This program does not authorize replacing Agent Memory with any external system, vendor lock-in, treating emerging drafts as adopted standards, importing external schemas without semantic review, inventing a universal memory score, averaging critical governance failures into a passing aggregate, weakening scope, privacy, correction, or deletion semantics for implementation convenience, or declaring cumulative implementation conformance merely because ADR-020 is accepted.

Program completion also does not imply that #5, #67, #68, repository-governance work, deployment-specific telemetry work, or future architecture-family evidence is complete.

## Governing principle

> Agent Memory is judged by what retained state is allowed to change in future behavior, under what authority, with what evidence, and whether the consequence can be reconstructed and undone or forgotten when required.

Retrieval quality matters. Governance is why this repository exists.
