# Derivation Provenance and Authority-Laundering Profile

Status: V0.1 reference profile for #204.

## Purpose

Summaries, restatements, compression, synthesis, and other transformations can create useful derived evidence. They do not create a new source origin or memory authority merely because the transformer is trusted, capable, or confident.

The governing boundary is:

```text
trusted transformer
!= trusted source

transformation
!= independent corroboration

derived confidence
!= authority

repetition / re-summarization
!= new independent origin
```

This profile defines a small derivation evidence envelope that preserves the original evidence lineage through one or more transformations and leaves durable-state authority to the normal PAMA path.

## Structural basis

The existing fixture [`../../fixtures/authority-laundering.json`](../../fixtures/authority-laundering.json) requires:

```text
origin_preserved = true
transformation_grants_authority = false
durable_promotion_allowed = false
```

The fixture also states:

```text
origin_survives_transformation
trusted_tool_echo_not_equal_trusted_origin
authority_not_laundered_through_summary
```

V0.1 converts those structural requirements into executable behavior.

## Derivation evidence envelope

The schema is [`../../schemas/derivation-evidence.schema.json`](../../schemas/derivation-evidence.schema.json).

A record preserves:

```text
profile_version
derivation_id
root_origin_refs
immediate_source_refs
source_trust
transformation
prior_derivation_refs
derivation_depth
scope
evidence_refs
optional confidence evidence
binding
created_at
interpretation
```

### Root origin

`root_origin_refs` identifies the evidence origin that existed before the transformation chain.

A later derivation inherits that list exactly.

```text
source A
 -> summary B
 -> compressed summary C

root origin of B = A
root origin of C = A
```

B and C are useful derived artifacts, but neither becomes an independent source merely by existing.

### Immediate source

`immediate_source_refs` identifies what the current transformation directly consumed.

For a first-order summary this may be the original memory/evidence reference. For a second-order transformation it is the prior `derivation_id`.

This permits reconstruction of both:

```text
root origin
and
transformation chain
```

without treating every intermediate artifact as independent corroboration.

## Transformer provenance

The transformation block preserves:

```text
method
transformer_ref
transformer_version
transformer_trust
output_ref
```

Transformer trust is evidence about the transformation process. It is not a rewrite of source trust.

```text
source_trust = untrusted
transformer_trust = trusted

result source_trust = untrusted
```

A trusted summarizer may faithfully summarize an untrusted claim. That makes the transformation potentially useful. It does not make the claim authoritative.

## Confidence and estimator evidence

A transformation may preserve bounded confidence information:

```text
signal_semantics
estimator_ref
estimator_version
value
```

The interpretation is fixed:

```text
confidence_authority = none
```

The behavioral harness sends otherwise identical crystallization proposals with confidence `0.99` and `0.01` and requires the same PAMA authority envelope.

## Fixed non-authority interpretation

Every normalized derivation records:

```text
authority_effect = none
memory_admission = not_established
certification_claim = none
transformer_authority = none
confidence_authority = none
source_trust_authority = none
independent_corroboration = not_established
repetition_creates_independent_origin = false
root_origin_preserved = true
```

These fields are not predictions. They define the boundary of the derivation record itself.

## Authority-shaped input is discarded

The normalizer consumes a bounded allowlist of provenance fields.

Caller-supplied fields such as:

```text
pama_outcome
authority
certification
lifecycle_state
source_trust_override
raw_prompt
hidden_reasoning
```

have no output path.

A transformer therefore cannot smuggle a permission or lifecycle claim into the derivation envelope by choosing an impressive field name.

## Scope binding

A derivation preserves:

```text
scope_ref
tenant_ref
project_ref
```

When an expected scope is supplied, the envelope records:

```text
binding.status = exact | mismatch
```

with explicit mismatch reasons.

Cross-tenant or cross-project evidence remains evidence, but it is not silently treated as an in-scope candidate.

Later derivations inherit the prior scope. A later transformer cannot rewrite the source scope through transformation metadata.

## Replay and repetition

The derivation identifier is deterministic over the normalized transformation evidence.

The same exact derivation replay therefore produces the same `derivation_id`.

```text
same transformation replay
!= second independent source
```

A later transformation gets a new derivation identifier because a new transformation occurred, while retaining the same root origin and append-only prior-derivation lineage.

## Behavioral PAMA proof

The V0.1 harness is [`../../reference/agentmem_ref/authority_laundering_harness.py`](../../reference/agentmem_ref/authority_laundering_harness.py).

It performs this sequence:

```text
untrusted origin
 -> trusted summary
 -> derived evidence envelope
 -> trusted second transformation
 -> same untrusted root origin retained
 -> high-consequence crystallization proposal
 -> normal PAMA evaluation
 -> external verification still required
 -> crystallization prohibited
 -> zero durable substrate writes
```

The PAMA decision and decision receipt retain the derivation and origin evidence references even though the requested crystallization does not commit.

Blocking a consequence therefore does not erase why the system blocked it.

## No transformer-specific ontology

V0.1 does not define an LLM, summarizer, compression engine, or model-specific schema.

A transformer only needs to supply bounded provenance:

```text
who transformed
which version
how
what source was consumed
what output reference was produced
what evidence supports the transformation
```

The Agent Memory authority model remains unchanged.

## Evidence depth

The dedicated report uses the repository D/F/H/R/P vocabulary:

```text
D = memory threat model + adapter doctrine + this profile
F = authority-laundering fixture
H = executable derivation + PAMA harness
R = explicitly unproven
P = explicitly unproven
```

The reference harness does not execute a live external summarization system, so it does not claim runtime `R` evidence.

No production evidence is collected, so `P` remains unproven.

## Privacy and minimization

The derivation envelope contains references and bounded estimator metadata. It does not require:

- raw prompts;
- hidden reasoning;
- full source content;
- full transformed output;
- credentials;
- arbitrary model traces.

Content may be retained elsewhere according to normal memory/evidence policy. This envelope only needs stable references sufficient to reconstruct provenance.

## Deployment profiles

### L: local

Local summarizers or deterministic transformations can use the same envelope. Local execution does not make the transformer authoritative.

### T: team / multi-tenant

Tenant and project identity must survive transformation. A shared summarizer cannot collapse distinct tenant origins into one authority state.

### E: enterprise

Transformer identity/version and evidence custody should be reconstructable. Changes in transformation service do not rewrite old origin state.

### H: high assurance

Root origin, transformation chain, exact scope, estimator provenance, PAMA decision, and non-authority interpretation must remain independently reconstructable. Missing origin identity fails closed.

## Non-claims

V0.1 does not establish:

- semantic truth of a summary;
- certification of a transformer;
- independent corroboration from restatement;
- durable-memory admission;
- permission to crystallize a derived claim;
- runtime resistance for arbitrary external summarization services;
- production security certification.

## Stop line

Do not turn derivation metadata into a second authority system. If a transformed claim needs durable authority, it must enter the existing governance path with the source lineage still attached.
