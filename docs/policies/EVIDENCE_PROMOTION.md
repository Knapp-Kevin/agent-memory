# Evidence and Doctrine Promotion Policy

Status: Active repository policy when merged

## Purpose

Agent Memory evaluates claims by evidence and consequence, not by the identity or prestige of the source that supplied them.

> **Origin establishes provenance, not evidentiary privilege.**

This rule is source-neutral. It applies equally to native Agent Memory doctrine, maintainer statements, contributor proposals, AI-generated analysis, practitioner feedback, external implementations, research papers, standards, benchmark results, production observations, and external corpora such as Agent Memory Atlas.

## Core distinction

Every material claim should keep three questions separate:

```text
Who or what produced the claim?   -> provenance
What evidence supports it?        -> epistemic status
What may it change or authorize?  -> governance consequence
```

None answers either of the other two.

Authorship does not prove correctness. Publication does not prove correctness. Popularity does not prove correctness. Deployment does not prove correctness outside the observed boundary. A passing validator does not prove more than the validator's declared contract. AI generation does not weaken or strengthen a claim by itself.

## Claim record

Where a claim may materially affect doctrine, contracts, conformance, security, privacy, lifecycle behavior, authority, or production guidance, record enough information to reconstruct its status:

```text
claim
origin / provenance
claim type
evidence class
supporting evidence
challenging evidence
reproduction status
scope / boundary conditions
known counterexamples
promotion state
```

The representation may vary by research program. The distinctions may not be collapsed.

A reusable record is available at [`../templates/claim-evidence-record.md`](../templates/claim-evidence-record.md). Research programs may extend it with domain-specific fields while preserving the source-neutral distinctions above.

## Evidence classes

Useful evidence classes include:

- `hypothesis`: a falsifiable candidate that has not yet been demonstrated;
- `architectural_deduction`: a conclusion derived from stated premises and contracts;
- `implementation_observation`: behavior inspected in a specific implementation/version;
- `external_empirical_evidence`: an externally produced observation or experiment;
- `conformance_evidence`: evidence against a declared conformance contract;
- `runtime_evidence`: executed behavior from a pinned runtime/substrate and scenario;
- `benchmark_evidence`: results from a pinned dataset, harness, evaluator, and configuration;
- `production_evidence`: observations from an identified production boundary.

These are not a universal scalar ranking. Evidence strength is claim-specific.

Examples:

```text
A benchmark can strongly support a benchmark-scoped comparison
while proving little about production isolation.

A runtime fixture can prove one negative path
without proving every storage architecture.

A production incident can prove a failure occurred
without proving a proposed root cause.
```

## Source-neutral challenge rule

Material claims should be challengeable regardless of origin.

That includes claims already present in Accepted ADRs. Accepted means the decision is currently adopted for its documented scope. It does not mean later contradictory evidence is inadmissible.

For consequential claims:

1. identify what would falsify or materially narrow the claim;
2. seek credible contradictory evidence where practical;
3. preserve negative results and counterexamples;
4. distinguish inability to reproduce from proof of absence;
5. change doctrine only when the evidence and consequence justify it.

Do not manufacture false balance. A weak contradiction does not cancel strong evidence merely because both exist.

## Reproduction and promotion

An input may be valuable before it is proven. It can generate:

- a hypothesis;
- an adversarial fixture;
- a comparator;
- a threat scenario;
- a research question;
- a candidate implementation pattern.

That is not the same as doctrine promotion.

A typical path is:

```text
input
 -> claim / hypothesis
 -> primary-source inspection where applicable
 -> local reproducer or independent evidence where applicable
 -> supporting and challenging evidence
 -> scoped conclusion
 -> doctrine / contract / ADR proposal
 -> validation at the consequence-appropriate boundary
```

Not every claim needs every step. Editorial facts do not require a research program. High-consequence security, authority, lifecycle, deletion, privacy, or conformance claims require stronger evidence than low-risk explanatory text.

## External corpora and field guides

External surveys, catalogs, field guides, and repositories may efficiently surface patterns that deserve testing. Their aggregation does not confer authority.

For example, Agent Memory Atlas may be recorded as:

```text
source role: discovery / external evidence
claim status: unverified until inspected or reproduced
possible output: adversarial fixture or architecture comparison
```

The same treatment applies to any other source. There is no Atlas-specific skepticism rule and no native-Agent-Memory exemption.

## AI-assisted analysis

AI systems may search, synthesize, compare, propose, implement, and test under repository policy. Model output is a proposal/evidence-processing artifact, not an epistemic shortcut.

A model stating that a paper, repository, benchmark, test, or prior ADR proves something does not make that statement true. The underlying evidence and its boundary remain the decision input.

## Validator boundary

A passing automated check establishes only what the check actually exercised at the tested revision.

Preserve the distinction:

```text
CI green
!= runtime behavior universally proven
!= production outcome proven
!= architecture-independent conformance
!= doctrine correctness proven
```

Exact-head requirements remain exact-head requirements. A later revision does not inherit evidence automatically.

## Promotion outcomes

A researched claim may result in:

- **no change**: current doctrine survives the challenge;
- **clarification**: doctrine was correct but underspecified;
- **boundary narrowing**: the claim holds only under identified conditions;
- **new fixture or conformance requirement**: the failure is real but doctrine already covers it;
- **candidate doctrine change**: current doctrine is insufficient;
- **supersession/rejection**: stronger evidence invalidates an earlier decision for its stated scope.

Recording a no-change result is useful evidence. Research is not required to produce novelty to justify its existence.

## Governing principle

> **Who said it is provenance. What proves it is evidence. What it may change is governance.**
