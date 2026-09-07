# Runtime Evidence

**[Conformance and Evidence](Conformance-and-Evidence)** describes the evidence ladder. This page records where Agent Memory actually stands on it.

The distinction this page exists to protect: a repository can validate perfectly and still have demonstrated nothing about runtime behavior. Everything below is labelled by what it genuinely establishes.

## The evidence bar

A claim counts as runtime evidence only when all five hold:

| Requirement | Meaning |
|---|---|
| **Executed** | the path ran against a real substrate or executable reference boundary, not a diagram |
| **Pinned** | substrate/comparator, adapter, policy, estimator, fixture, and direct validation versions are recorded where applicable |
| **Reproducible** | another operator re-runs it and gets the same verdict |
| **Negative-tested** | the run includes paths that must fail, and they failed |
| **Reconstructable** | a receipt/evidence chain reconstructs estimate, authority, selection, consequence, and applicable lifecycle result |

Evidence that omits the negative paths is a demo. Evidence that cannot be re-run is an anecdote. Neither moves an Architecture Decision Record by itself.

## What has been demonstrated

A reference governed adapter executes the full path — proposal, authority envelope, permitted action set, selected action, substrate mutation, decision receipt, retrieval, governed admission — and runs in continuous integration.

**Against a real temporal knowledge graph.** Governance paths execute against a live graph database with no language model, no embedder, no API key, and no server. This includes cross-partition refusal, supersession that marks rather than deletes, pruning that keeps content recoverable, and a physical delete.

**Against the doctrine fixture corpus.** Repository fixtures are driven through the adapter's own authority-enforcement rule. This matters because the fixtures were written to describe doctrine, not to satisfy the adapter, so agreement between them is evidence rather than a test suite agreeing with its author.

**Stochastic containment.** Repeated trials sample from the permitted action set. No trial may select outside the envelope, and a deliberately hostile selector that tries to take a prohibited action is contained by the adapter rather than trusted to behave.

**Canonical/derived deletion completeness.** The P4 evidence path computes projection staleness and residue, traverses transitive purge closure, independently sweeps for surviving residue, refuses unauthorized estimator-mediated rebuild, and distinguishes residual failure from zero-undeclared-residue success.

**Portable governance evidence.** P4.5a/b/c executes a content-free signed projection of the canonical Agent Memory receipt, Agent Manifest checkpoint correlation, TRACE/cMCP external-action evidence correlation, lifecycle-result composition, and authority/domain-continuity negative paths. This is evidence toward ADR-021, not acceptance of it.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/portable-evidence-chain-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/portable-evidence-chain-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/portable-evidence-chain-flow-light.svg" alt="Portable Agent Memory governance evidence chain showing the canonical decision receipt, content-free signed evidence projection, correlation to runtime and Agent Manifest or TRACE-cMCP evidence, and independent verification of evidence integrity, governance disposition, runtime execution, and lifecycle satisfaction" width="100%">
  </picture>
</p>

The diagram is an **evidence-scoped explanatory surface**, not adopted ADR-021 doctrine. The canonical Agent Memory receipt remains authoritative for memory semantics and PAMA. Portable evidence can prove integrity and correlation without receiving raw memory, but a valid signature does not create permission, a valid execution does not establish authorization, and a valid `DEL` does not establish forgetting completeness. The four verifier dimensions remain separate so valid negative outcomes are representable rather than flattened into a reassuring but useless `valid = true`.

## What that still does not prove

Stated plainly, because a partial result presented as a complete one is worse than no result:

- **No conformance level is raised by these diagrams or evidence slices.** Levels remain governed by their cumulative requirements.
- The reference adapter remains a narrow evidence vehicle rather than a production Agent Memory implementation.
- Retrieval-quality calibration, production trust discovery, universal key/revocation infrastructure, and physical-media erasure are not established by P4/P4.5.
- P4.5 does not establish upstream AgenTrust integration acceptance or multi-implementation interoperability beyond the pinned comparators exercised locally.
- ADR-020, ADR-021, and ADR-022 remain independently maturity-gated. Executing supporting evidence does not accept them automatically.

## Why the tests are built to fail

Two habits distinguish this evidence from self-congratulation.

**The substrate model is permissive on purpose.** It reproduces mapped substrate behavior including dangerous defaults. Tests assert both that the substrate would permit problematic behavior and that the governed adapter refuses regardless. A test that only checked the adapter would not show the governance was doing any work.

**The checkers are mutation- and adversarially tested.** Deliberately corrupted authority envelopes, wrong action references, replay, trust failures, stale authority/domain state, unauthorized broadening, and deletion residue must be detected. A conformance check that cannot fail is decoration, so negative cases remain permanent evidence.

## What execution corrected

Execution has repeatedly narrowed claims that source reading or a polished diagram could otherwise overstate. Examples include substrate defaults that return invalidated facts, deletion paths whose raw operation succeeds while derived residue survives, and portable evidence that remains cryptographically valid even when execution-time domain authority has been revoked.

Those are precisely why the architecture separates retrieval from admission, delete operation from lifecycle satisfaction, evidence integrity from governance disposition, and decision-time authority from execution-time continuity.

## Where this leaves emerging ADRs

Closer, and deliberately not declared complete by visualization.

- **ADR-020 is Accepted.** P4 executes a substantial deletion-completeness evidence bar.
- **ADR-021 remains Proposed.** P4.5 local implementation is complete and supplies executable evidence for the portable boundary, including Agent Manifest and TRACE/cMCP correlation, but ADR acceptance remains a separate decision.
- **ADR-022 is Accepted.** Isolation-domain evidence is recorded under `docs/audits/isolation/` (issue #68 gap reconciliation).

## Canonical and evidence sources

- Runtime evidence program: https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/docs/programs/runtime-evidence
- Portable governance evidence: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/programs/runtime-evidence/portable-governance-evidence.md
- Canonical and derived state: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/programs/runtime-evidence/canonical-and-derived-state.md
- Substrate capability mapping: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/programs/runtime-evidence/graphiti-conformance.md
- Reference adapter and verifiers: https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/reference
- Proposed ADR-021: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-021-portable-memory-governance-evidence-boundary.md
- Conformance test plan: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/06-conformance-test-plan.md

## Next

- **[Conformance and Evidence](Conformance-and-Evidence)** for the full evidence ladder and level definitions
- **[Canonical and Derived State](Canonical-and-Derived-State)** for deletion propagation and residue
- **[Implementation Guide](Implementation-Guide)** to map your own runtime
- **[Governed Uncertainty](Governed-Uncertainty)** for the doctrine these paths test
