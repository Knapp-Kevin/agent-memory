# ADR-026: Origin Is Provenance, Not Evidentiary Authority

Status: Proposed

Date: 2026-08-12

## Context

Agent Memory consumes heterogeneous inputs: native doctrine, maintainer decisions, contributor proposals, AI-generated analysis, practitioner feedback, research papers, standards, source code, benchmarks, conformance fixtures, runtime evidence, production observations, and external corpora.

The repository already distinguishes evidence classes and requires explicit evidence for doctrine changes. However, parts of the repository frame the strongest skepticism rules around external sources. That leaves an avoidable ambiguity: a native or maintainer-authored claim could appear to receive more epistemic privilege merely because it originated inside the project, while an external paper or implementation could appear authoritative merely because it is published or widely used.

Issue #146 makes the repository-wide rule explicit.

## Decision

The origin of a claim establishes its **provenance**. It does not establish its correctness, evidence strength, doctrine status, or authority.

Material claims must be evaluated using source-neutral evidence and consequence-appropriate promotion gates.

This applies equally to:

- native Agent Memory doctrine;
- maintainer and contributor claims;
- existing and Accepted ADRs;
- AI-generated analysis or implementation proposals;
- practitioner/community reports;
- research publications and standards;
- external implementations and corpora;
- benchmarks and evaluators;
- runtime and production observations.

The repository must preserve three distinct questions:

```text
origin / provenance
        !=
evidence / epistemic status
        !=
governance / permitted consequence
```

An Accepted ADR records the currently adopted decision for its stated scope. It is not immune to later contradictory evidence. Stronger evidence may clarify, narrow, supersede, or reject an earlier decision through the normal decision trail.

## Rationale

Source-specific privilege creates predictable failure modes:

- maintainer intuition can become doctrine without sufficient challenge;
- published work can be imported beyond the scope it actually proves;
- benchmark scores can masquerade as production assurance;
- AI output can be accepted or dismissed based on origin rather than verification;
- prior decisions can become self-protecting because they are already canonical;
- popular implementation patterns can acquire authority through repetition rather than evidence.

A source-neutral rule does not imply that every source has equal reliability. Source quality, study design, reproducibility, implementation version, independence, and scope remain relevant evidence characteristics. The rule is that those properties must be evaluated rather than inferred from source identity alone.

## Consequences

### Positive

- Internal and external claims face the same epistemic discipline.
- Native authorship remains clear without becoming a truth claim.
- External sources can challenge doctrine without automatically replacing it.
- AI assistance remains usable without becoming an epistemic shortcut.
- Accepted doctrine can evolve when evidence changes.
- Negative results and failed reproductions remain useful outputs.

### Negative

- Doctrine changes may require more explicit evidence bookkeeping.
- Maintainer certainty cannot substitute for a consequence-appropriate validation path.
- Popular or prestigious sources may still require local boundary analysis.
- Some research work will legitimately end with no doctrine change.

## Implementation

The repository should maintain the policy in `docs/policies/EVIDENCE_PROMOTION.md` and link it from `GOVERNANCE.md`.

Material research records should be able to distinguish at least:

```text
claim
provenance
evidence class
supporting evidence
challenging evidence
reproduction status
scope / boundary conditions
promotion state
```

The exact storage format is not architectural doctrine.

## Validation and acceptance

This ADR remains Proposed until:

- repository governance text consistently expresses the source-neutral rule;
- #67 and #138 research promotion paths can apply the rule without special-case source privilege;
- at least one research cycle demonstrates preservation of an input as a hypothesis without premature doctrine promotion;
- contradictory or negative evidence can be recorded without being treated as repository-policy failure;
- review confirms that this ADR does not weaken authorship, licensing, source-rights, or repository authority rules.

## Related

- #146
- #67
- #138
- ADR-020: Probabilistic Discovery, Deterministic Governance
- `GOVERNANCE.md`
- `docs/08-source-material-index.md`
- `docs/policies/EVIDENCE_PROMOTION.md`
