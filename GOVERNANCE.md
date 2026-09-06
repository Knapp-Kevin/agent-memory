# Repository Governance

Agent Memory is a public reference architecture with one canonical doctrine tree, not a collection of equally authoritative implementation opinions.

## Stewardship and maintainer

The repository is stewarded by **MythologIQ Labs LLC** through `MythologIQ-Labs-LLC/agent-memory`.

The current repository maintainer and doctrine owner is **Kevin R. Knapp** (`@Knapp-Kevin`). Organization stewardship does not rewrite individual authorship provenance.

PAMA is native Agent Memory doctrine authored by Kevin R. Knapp. External implementations may conform to, challenge, or extend the doctrine through the contribution process, but they do not acquire doctrine ownership by implementing it.

## AI-assisted contribution authority

Agent Memory adopts [`docs/policies/AI_ASSISTED_CONTRIBUTIONS.md`](docs/policies/AI_ASSISTED_CONTRIBUTIONS.md) as its repository policy for AI-assisted development and human-directed agent execution.

The policy separates implementation method from repository authority:

- coding agents and AI-assisted development are allowed;
- contributors and maintainers are not required to hand-write code or manually perform every repository API action;
- a responsible human remains accountable for the objective, material risk, and delegated authority;
- authenticated agents may perform repository actions when directly delegated in a bounded working session or authorized by standing repository policy;
- unbounded autonomous contribution is not accepted by default;
- direct delegation inside Agent Memory does not create authority to act in external repositories;
- upstream contribution rules control when they are stricter.

Agent Memory's policy is authoritative only for this repository. Organization-wide contribution-policy inheritance is governed outside this repository and is not implied by local adoption.

DCO is not an active Agent Memory gate until explicit activation and enforcement are merged and discoverable.

## Decision classes

Changes are reviewed according to their consequence.

### Editorial

Examples:

- grammar and formatting;
- clearer examples;
- corrected links;
- non-semantic navigation improvements.

These should not change doctrine meaning.

### Evidence

Examples:

- new research;
- benchmark results;
- source-rights records;
- implementation mappings;
- adversarial fixtures;
- runtime evidence.

Evidence may support, challenge, or narrow existing doctrine. Adding evidence does not automatically change an ADR.

### Contract

Examples:

- schema changes;
- fixture-semantic changes;
- conformance-level changes;
- adapter contracts;
- telemetry/interchange contracts;
- PAMA machine-readable interfaces.

Contract changes require compatibility analysis and validation updates.

### Doctrine / ADR

Examples:

- changing an architectural invariant;
- changing the meaning of PAMA authority classes;
- changing lifecycle semantics;
- accepting, superseding, or rejecting an ADR.

Doctrine changes require explicit rationale, affected-surface analysis, evidence, and a preserved decision trail.

## Evidence rule

Agent Memory adopts [`docs/policies/EVIDENCE_PROMOTION.md`](docs/policies/EVIDENCE_PROMOTION.md) as the source-neutral evidence and doctrine-promotion policy.

> **Origin establishes provenance, not evidentiary privilege.**

This applies to every material input, including native doctrine, maintainer or contributor statements, AI-generated analysis, practitioner feedback, external research, standards, implementations, benchmarks, production observations, and external corpora.

A merged statement should make its epistemic status clear.

Where material, distinguish:

```text
native doctrine
external evidence
implementation observation
conformance evidence
runtime proof
hypothesis
analogy
```

Native authorship establishes provenance and repository ownership of a decision. It does not prove the decision correct. External publication or popularity does not prove a claim correct either. Accepted ADRs remain challengeable and may be narrowed, superseded, or rejected when stronger evidence justifies a change.

A validator passing is evidence about the validator's declared contract. It is not automatic proof of production behavior.

## Public-source and reuse-rights rule

Contributors must follow `docs/SOURCE_RIGHTS_POLICY.md`.

Public availability does not imply permission to copy expressive material. External sources should normally be linked and independently synthesized unless a stronger reuse basis is both necessary and documented.

## Merge expectations

A change is merge-ready when:

1. the intended consequence is explicit;
2. affected doctrine and contracts are internally consistent;
3. source provenance and reuse rights are resolved;
4. tests/validators relevant to the change pass;
5. repository authority for any agent-executed action is bounded and accountable;
6. any explicitly active contribution-provenance requirement is satisfied;
7. the PR distinguishes what it proves from what remains unproven;
8. material disagreement is either resolved or recorded rather than silently erased.

Where a task specifies exact-head validation, that validated head is the merge boundary. A later head must be revalidated rather than inheriting trust from an earlier result.

## Implementation neutrality

Named products and repositories appear in Agent Memory only when they add a concrete implementation, comparison, interoperability, or conformance value.

Conceptual adjacency does not create architectural ownership.

## Security-sensitive changes

Security-sensitive findings should follow `SECURITY.md`. Do not force public disclosure merely to satisfy normal issue-tracking ceremony.

AI assistance does not reduce the review bar for cryptography, authentication, authorization, policy enforcement, isolation boundaries, provenance, destructive lifecycle actions, or other security-sensitive surfaces. Independent validation is required when self-referential tests could mask an implementation error.

## Forks and derivative works

The Apache-2.0 license permits forks and derivative works under its terms. A derivative project may change its own doctrine, but it should not present modified doctrine as an unchanged canonical decision of this repository.

The canonical upstream doctrine is the state merged into `MythologIQ-Labs-LLC/agent-memory` unless an explicit release or version reference says otherwise.
