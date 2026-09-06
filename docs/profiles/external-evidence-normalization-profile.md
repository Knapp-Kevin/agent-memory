# External Trust and Attestation Evidence Normalization Profile

## Status

Reference V0.1 implementation profile for issue #180, now exercised against two materially different real peer families: TRACE and cMCP.

## Purpose

This profile defines the smallest vendor-neutral boundary for accepting external identity, trust, attestation, decision, enforcement, execution, runtime, or delegation evidence as an Agent Memory evidence candidate without importing peer authority.

The core invariants are:

```text
payload parsed
!= signature / claim verified
!= claim current
!= claim applicable to this subject/action/scope
!= Agent Memory authority
```

and:

```text
verified identity
!= memory authority

valid attestation
!= semantic correctness

policy / decision evidence
!= enforcement evidence

execution evidence
!= lifecycle obligation satisfaction
```

The normalizer exists to preserve those distinctions in executable form.

## Layering

```text
peer-specific record
  -> peer adapter / verifier result
  -> vendor-neutral external evidence normalizer
  -> Agent Memory evidence candidate
  -> normal provenance / scope / lifecycle / PAMA handling
```

The reference implementation begins at the adapter/verifier-result boundary. It does not parse arbitrary peer wire formats and does not perform peer cryptography itself.

That split is intentional. A peer adapter may understand peer vocabulary and wire details. Canonical Agent Memory evidence semantics must not.

## Pinned reference peers

### TRACE

TRACE is the first reference comparator because the repository already has executable TRACE/cMCP evidence work and an exact release pin.

```text
peer:                TRACE
TRACE SDK:           agentrust-trace==0.9.0
TRACE release ref:   94271a1630601c94e80a23263d9750cb8d39f1f4
reference contract:  TRACE action-receipt verification / external action-evidence surface
```

This reuses the existing P4.5c pin documented in `docs/programs/runtime-evidence/trace-action-evidence.md`.

TRACE remains a comparator. It is not a required Agent Memory runtime dependency and does not define Agent Memory vocabulary.

### cMCP

The second materially different peer is cMCP `v0.4.0`:

```text
peer:                cMCP
runtime package:     cmcp-runtime==0.4.0
cMCP release commit: a2e95151356c9ae6c545330c900f3d4af0e447c1
verifier:            cmcp_verify.verify_trace_claim
reference contract:  GatewayClaim enforcement/configuration + runtime-attestation evidence
```

cMCP differs from the first TRACE-shaped evidence comparator because one signed GatewayClaim can carry multiple independently verifiable evidence layers at once: policy bundle identity, audit-chain evidence, declared enforcement mode, runtime measurement, attestation posture, and optional Agent Manifest identity.

The V0.1 cMCP adapter therefore proves that one peer record may normalize into more than one generic evidence record without collapsing those evidence layers into one global trust boolean.

A different TRACE/cMCP version, release ref, or unsupported peer is preserved as source metadata but receives `applicability.status = unsupported` until an implementation explicitly validates that exact version.

## Adapter/verifier input boundary

The normalizer consumes a bounded result containing the facts needed for evidence interpretation, including:

```text
parse_status
source_peer
source_version
source_release_ref
record_ref
evidence_digest
adapter_id / adapter_version
issuer_id / signer_id
verifier_id
verification_status
verification_method
claim_type
claim_scope
subject_ref
tenant_ref
resource_ref
action_ref
runtime_ref
configuration_ref
policy_ref
decision_ref / decision_disposition
enforcement_posture
execution_posture
attestation_mode
delegation_ref
issued_at / expires_at
revocation_status / revocation_evidence_ref
evidence_refs
explicit limitations / non-claims
```

The input is not automatically durable state. It is material supplied to the normalizer by a peer-specific adapter or verifier.

Unknown peer-only fields are ignored. In particular, a peer cannot widen Agent Memory authority by adding fields that resemble:

```text
pama_outcome
permitted_actions
lifecycle_state
trust_score
```

Those fields do not enter the normalized output.

## Normalized evidence candidate

Schema:

`schemas/external-evidence-normalized.schema.json`

Reference implementation:

`reference/agentmem_ref/memory/external_evidence.py`

The normalized candidate contains distinct surfaces for:

```text
source provenance
issuer / signer identity
verification state
claim identity and scope
freshness
revocation
current-context applicability
stable evidence digest / references
explicit interpretation non-claims
```

The V0.1 interpretation block is deliberately fixed:

```json
{
  "authority_effect": "none",
  "memory_authority": "not_established",
  "semantic_correctness": "not_established",
  "lifecycle_satisfaction": "not_established"
}
```

A consumer that needs to make an Agent Memory mutation decision must still use normal Agent Memory provenance, trust, scope, lifecycle, and PAMA logic. The normalized evidence candidate is evidence input, never a bypass token.

## Verification state

Verification remains explicit:

```text
verified
failed
unknown
not_performed
unavailable
```

Schema-valid or successfully parsed evidence is never promoted to `verified` by the normalizer.

A failed verification produces an invalid applicability result.

Unknown, not-performed, or unavailable verification produces insufficient evidence rather than optimistic acceptance.

### Claim-scoped verification from cMCP

cMCP's released verifier reports a global status together with `verified_fields`, `unverified_fields`, and a failure reason. Agent Memory does not copy the global label blindly into every evidence layer.

For example, a real software-only cMCP claim can verify:

```text
schema
signature
trusted_public_key
policy_bundle.hash
tool_catalog.hash
attestation_freshness
audit_chain
```

while also reporting:

```text
hardware_attestation = unverified
cMCP global status   = partially_verified
```

The adapter can therefore emit:

```text
enforcement/configuration evidence = verified/applicable
runtime hardware-attestation evidence = unknown/insufficient_evidence
```

provided the enforcement/configuration evidence is independently bound by the exact released verifier result.

This is not a relaxation. It is stricter evidence typing. The hardware layer is not allowed to inherit verification from the policy/signature layer, and the policy/signature layer is not falsely erased merely because hardware evidence is absent.

## Freshness and revocation

Freshness and revocation are independent dimensions.

Freshness:

```text
current
expired
not_yet_valid
```

Revocation:

```text
not_revoked
revoked
unknown
```

Expired or revoked evidence is stale even when its historical signature remains valid.

Unknown revocation state remains unknown and prevents V0.1 from reporting the evidence as fully applicable.

Historical evidence may remain reconstructable after expiry or revocation. That historical reconstructability is not current authority.

### Claim freshness is not attestation freshness

The real cMCP comparator exposed a useful temporal distinction.

A GatewayClaim may be newly signed while carrying older attestation evidence. Therefore:

```text
GatewayClaim issued_at
!=
attestation_generated_at
```

and:

```text
attestation expiry
must not retroactively expire a newly issued policy/configuration evidence record
```

The cMCP adapter emits the signed enforcement/configuration record with the GatewayClaim `trace.iat`, while the attestation record uses its own generated-at plus validity window.

A stale attestation may therefore become historical/stale while independently verified current claim/signature/policy evidence remains current. This distinction is claim-scoped and does not imply that stale hardware evidence is acceptable as current hardware assurance.

## Applicability

The normalizer compares evidence binding against the current Agent Memory context supplied by the consumer.

V0.1 supports:

```text
applicable
mismatch
stale
unsupported
insufficient_evidence
invalid
```

At minimum, the current context can bind:

```text
subject_ref
scope
tenant_ref
resource_ref
action_ref
```

When the current context requires a binding and the evidence omits it, V0.1 reports a mismatch rather than assuming equivalence.

Examples:

```text
verified signature + wrong scope       -> mismatch
verified signature + wrong tenant      -> mismatch
verified signature + wrong action      -> mismatch
verified + expired                      -> stale
verified + revoked                      -> stale
unknown verification                    -> insufficient_evidence
failed verification                     -> invalid
unsupported source/version              -> unsupported
exact/current/verified/not-revoked      -> applicable
```

`applicable` means the evidence is applicable as evidence to the supplied context. It does not mean the underlying memory action is authorized.

## Claim-layer separation

The normalized claim may preserve independently supplied references or postures for:

```text
decision
enforcement
execution
runtime / configuration
identity / attestation
delegation
```

The normalizer does not manufacture missing layers.

For example, a valid decision record with no enforcement or execution claim remains decision evidence only. A runtime/configuration attestation remains evidence about runtime/configuration identity and does not become semantic correctness.

### cMCP enforcement posture is not execution evidence

The real cMCP adapter preserves the peer's three declared modes:

```text
enforce
advisory
silent
```

Those modes describe the gateway's configured/declared enforcement posture. Even `enforce` does not establish that a particular Agent Memory action executed or was prevented.

The cMCP adapter therefore does not populate `execution_posture` merely because the GatewayClaim says `enforce`.

## Privacy and minimization

V0.1 defaults to stable references and digests.

The normalized output does not require:

- raw prompts;
- raw memory content;
- full tool payloads;
- complete peer attestation bundles;
- peer signatures when a stable evidence digest/reference is sufficient for custody or later verification;
- peer-only authority vocabulary.

The cMCP real comparator specifically verifies that raw attestation evidence, quote signatures, certificate chains, and complete tool transcript entries do not escape into normalized records. Stable claim, audit-root/tip, policy-bundle, tool-catalog, and optional Agent Manifest references are sufficient for the bounded evidence candidate.

The source record remains independently referencable through `record_ref` and `evidence_digest` when policy permits retention or retrieval.

## Deployment profiles

### L: local / single-user / offline

The normalizer has no network requirement. A local caller may supply static or pre-verified adapter results. Unknown verification remains unknown rather than being silently upgraded because the deployment is local.

### T: team / multi-tenant

`subject_ref`, `scope`, and `tenant_ref` remain explicit. Cross-tenant evidence mismatches fail deterministically.

### E: enterprise

The verifier identity and verification method are explicit, allowing external attestation or identity services to supply verifier results without becoming mandatory core dependencies.

### H: high assurance

Peer/release version, verifier identity, freshness, revocation, exact context binding, evidence digest, and explicit non-claims remain reconstructable.

### X: cross-organization

Cross-organization delegation semantics are not a V0.1 completion target. A `delegation_ref` may be preserved as evidence, but it does not create delegated Agent Memory authority.

## Required negative paths

The generic fixture matrix covers:

- verified evidence with wrong scope;
- cross-tenant mismatch;
- wrong action binding;
- expired evidence;
- revoked evidence;
- unknown verification;
- verifier unavailable;
- failed verification;
- unknown revocation state;
- unsupported source/version;
- unsupported peer claim type;
- decision evidence without enforcement/execution claims;
- peer-only fields attempting to inject PAMA, lifecycle, or trust-score semantics;
- malformed/unparsed peer evidence;
- missing required current-context binding.

The real cMCP comparator adds:

- `enforce`, `advisory`, and `silent` posture preservation;
- software-only partial peer verification without hardware overclaim;
- stale attestation scoped to the attestation record;
- wrong approved policy hash producing invalid enforcement evidence;
- tampered signature producing invalid enforcement evidence;
- raw attestation/certificate material excluded from normalized evidence.

Generic fixture:

`fixtures/external-evidence-normalization-matrix.json`

Generic tests:

`reference/tests/test_external_evidence.py`

cMCP adapter tests and real comparator:

```text
reference/tests/test_cmcp_external_evidence.py
reference/run_cmcp_external_evidence_comparator.py
.github/workflows/cmcp-external-evidence.yml
```

## What the two-peer V0.1 evidence proves

Within the bounded reference implementation, fixtures, and real peer comparators, V0.1 demonstrates that:

- external trust/attestation evidence enters through an explicit vendor-neutral normalization boundary;
- exact peer version and release provenance remain reconstructable;
- parsing, verification, freshness, revocation, and applicability remain distinct;
- verified evidence cannot itself create Agent Memory authority;
- wrong-scope and cross-tenant evidence cannot become applicable silently;
- decision evidence is not upgraded into enforcement/execution evidence;
- runtime/configuration attestation does not establish semantic correctness;
- one rich peer record can produce multiple claim-scoped normalized evidence records without importing peer ontology into the generic schema;
- global peer verification status does not have to erase field-level evidence distinctions;
- software-only verification cannot become hardware attestation by association;
- stale attestation cannot silently become current hardware evidence;
- enforcement posture cannot manufacture execution evidence;
- raw peer payloads are unnecessary for the normalized candidate;
- unknown peer fields cannot widen PAMA or mutate canonical lifecycle state;
- removing the peer adapter leaves the normalized evidence contract understandable as generic evidence metadata.

The released cMCP comparator is runtime evidence for this adapter/verifier path. It is not production deployment evidence and does not prove universal cMCP assurance.

## What V0.1 does not prove

V0.1 does not prove:

- that TRACE, cMCP, or another peer is universally trustworthy;
- production key discovery, rotation, revocation, or trust-anchor policy;
- semantic correctness of an attested claim;
- Agent Memory mutation authorization;
- downstream enforcement merely because an enforcement posture exists;
- physical execution merely because an attestation exists;
- correction, deletion, forgetting, or other lifecycle obligation satisfaction;
- cross-organization delegation authority;
- compatibility with future TRACE/cMCP versions or unrelated peers;
- real TPM/SNP/TDX hardware assurance merely because the software-only comparator passed;
- production cMCP deployment;
- a need for a TRACE or cMCP core-schema change.

## Rollback / disable behavior

The normalizer and all peer adapters are optional evidence surfaces.

Disabling or removing a TRACE or cMCP adapter does not invalidate canonical Agent Memory records. Existing normalized records remain understandable through the vendor-neutral schema and retain their source/version/reference metadata.

No canonical memory object requires TRACE- or cMCP-only vocabulary to remain interpretable.

## Follow-on gate

The two-peer generic evidence gate is now satisfied by TRACE plus released cMCP v0.4.0.

A third peer should be added only when it tests a materially different evidence responsibility, not merely another signed identity document. Agent Manifest remains a reasonable future candidate for identity/configuration binding, but it should not be introduced simply to accumulate protocol coverage.

Cedarling research is separately evaluating whether its JWT/multi-issuer verification can become a useful identity-evidence source while its policy decision continues to use the already-proven external-policy seam. That work must preserve the same rule: verified identity is evidence, not Agent Memory authority.

Speculative breadth is not evidence.
