# Source Trust and Reputation

> Canonical requirement: [ADR-009](adr/ADR-009-source-trust-is-a-first-class-signal.md)

## Purpose

Memory quality depends not only on what a source says, but on what kind of source produced it, how reliably that source has behaved, what scope the reliability applies to, and whether later transformations preserve the source's origin.

Source trust is therefore a first-class evidence signal.

It is **not** authority.

```text
source trust -> evidence weighting
source trust != permission
source trust != certification
source trust != factual truth
```

## Why a trust layer exists

Without explicit source trust, memory systems tend to make one of two mistakes:

1. treat every observation as equally credible
2. smuggle source preference into opaque model behavior

Neither is acceptable for governed memory.

## Source classes

At minimum, implementations should distinguish:

- direct user statement
- user-approved correction
- authoritative policy or system record
- signed or verified artifact
- deterministic tool observation
- probabilistic tool/model inference
- external document or webpage
- organization-internal document
- agent-generated summary
- agent-generated inference
- another agent's assertion
- synthetic or simulated data
- unknown or unattributed source

Source class is not a universal trust ordering. Context matters.

A user statement may be authoritative about personal preference while weak evidence about an external scientific fact.

## Trust is multidimensional

A single scalar may be convenient but can hide important distinctions.

Useful dimensions include:

```text
identity_assurance
provenance_integrity
domain_competence
historical_reliability
independence
recency
scope_match
corroboration_quality
adversarial_exposure
transformation_distance
```

Implementations may use a scalar, vector, categorical model, or probabilistic distribution. They must declare what the representation means.

## Trust estimate record

A consequential source-trust estimate should preserve:

```text
source_id
source_class
trust_dimensions
trust_value_or_distribution
estimator_id
estimator_version
calibration_version
calibration_scope
evidence_refs
uncertainty
valid_scope
computed_at
expires_or_recheck_at
```

## Deterministic substrate

The following should be stable where required:

- source identity
- source-to-memory provenance links
- origin labels
- tenant/scope labels
- signature/hash verification results
- derivation relationships
- policy rules governing authority

Trust estimation may be probabilistic. Origin should not become probabilistic because a model likes the prose.

## Probabilistic trust

Trust may legitimately be inferred from:

- prior accuracy
- contradiction history
- domain-specific performance
- provenance quality
- corroboration
- anomaly signals
- freshness
- source behavior over time

A probabilistic trust estimate should remain an estimate.

Example:

```text
source_reliability = 0.86
```

must not silently become:

```text
source_is_authoritative = true
```

unless policy explicitly defines that transition and its scope.

## Latent source preference

LLMs may exhibit source preferences independent of explicit trust policy.

That creates a hidden trust channel:

```text
model prior
  -> source preference
  -> retrieval / synthesis weighting
  -> memory formation
```

Governed memory should therefore distinguish **declared trust policy** from **latent model preference**.

Possible controls:

- expose source identity during evaluation
- test counterfactual source labels
- compare content-equivalent sources
- record retrieval/ranking behavior by source class
- avoid treating model attention or selection frequency as evidence of reliability

## Independence and corroboration

Corroboration is useful only when evidence is sufficiently independent.

Wrong:

```text
agent summary A
agent restates A as B
another summary cites B
=> three sources
```

Correct:

```text
A -> B -> C share one origin lineage
independent_source_count = 1
```

Required rules:

- preserve derivation graphs
- detect self-citation loops
- distinguish independent witnesses from transformations
- prevent Sybil-style manufactured corroboration

## Trust decay and recovery

Trust may change with time and evidence.

Possible transitions:

```text
trusted -> degraded
unknown -> trusted-within-scope
trusted -> disputed
blocked -> rehabilitated
```

Changes should be evidence-driven and ledgered when consequential.

A source should not gain permanent global reputation because it performed well on one task family.

## Domain and scope specificity

Trust should be scoped.

Examples:

```text
source trusted for repository build status
source not authoritative for security policy

user authoritative for own preference
user not automatically authoritative for third-party identity
```

Cross-domain trust transfer should be explicit.

## Trust and authority

PAMA may consume source trust as one input.

It should also consider:

- requested consequence
- actor authority
- reversibility
- scope
- certification
- contradiction
- sensitivity
- provenance integrity

Example:

```text
high-trust source + low-risk reversible update -> may allow
high-trust source + permanent deletion -> still requires deletion authority
```

High trust does not eliminate consequence proportionality.

## Trust and memory lifecycle

Source trust may influence:

- admission
- saturation
- contradiction pressure
- verification priority
- retrieval ranking
- consolidation
- stale-state detection

It should not directly determine:

- identity
- certification
- cross-tenant permission
- permanent deletion
- policy mutation

## Trust and forgetting

Weak or deteriorating source trust may increase decay pressure, but automatic deletion can destroy evidence needed to explain why a source became untrusted.

Prefer a distinction between:

```text
reduced retrieval priority
archival
quarantine
dispute
retention for audit
irreversible deletion
```

## Trust attacks

Threats include:

- source spoofing
- trusted-tool echo
- provenance laundering
- manufactured corroboration
- self-citation
- reputation farming
- domain transfer abuse
- stale reputation reuse
- source-label manipulation
- model latent preference exploitation

## Conformance cases

### High-volume low-quality source

Expected:

```text
volume alone does not create high trust
```

### Trusted-tool echo

Untrusted content passes through a trusted tool unchanged.

Expected:

```text
content origin remains untrusted
```

### Manufactured corroboration

Several memories derive from one attacker-controlled source.

Expected:

```text
independent corroboration count does not inflate
```

### Domain mismatch

A source reliable for domain A makes a claim in domain B.

Expected:

```text
A-specific reputation not silently reused as B authority
```

### Latent preference counterfactual

Equivalent content is attributed to different source labels.

Expected:

```text
material ranking differences are measurable and do not silently redefine trust policy
```

### Trust uncertainty near high consequence

Expected:

```text
uncertainty may trigger verification or review
confidence does not manufacture authority
```

## Research signals

- [In Agents We Trust, but Who Do Agents Trust?](https://arxiv.org/abs/2602.15456) reports systematic latent source preferences in LLM agents, supporting explicit evaluation of hidden source weighting.
- [From Agent Traces to Trust](https://arxiv.org/abs/2606.04990) surveys evidence tracing and execution provenance, reinforcing the importance of provenance-bearing memory and process-level accountability.
- [Securing LLM-Agent Long-Term Memory Against Poisoning](https://arxiv.org/abs/2606.24322) challenges content- and lineage-only defenses when origin can be laundered through transformations, motivating stronger origin-bound authority semantics.
- [Belief Memory: Agent Memory Under Partial Observability](https://arxiv.org/abs/2605.05583) provides evidence that preserving multiple candidate beliefs and their probabilities can outperform collapsing ambiguous observations into deterministic conclusions.

## Doctrine

Trust is evidence about a source.

It is not a transferable permission token.

A mature memory system knows **who said it, how that source earned trust, where that trust applies, how uncertain it is, and what the trust is actually allowed to influence**.
