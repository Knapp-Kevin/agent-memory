# cMCP External Evidence Profile

## Purpose

This profile proves the inbound half of Agent Memory's evidence relationship with cMCP `v0.4.0`.

The repository already exercises the opposite direction through the released TRACE/cMCP audit-bundle comparator:

```text
Agent Memory portable governance evidence
-> TRACE action evidence
-> released cMCP verifier
```

This profile adds:

```text
released cMCP GatewayClaim + verifier result
-> cMCP-specific adapter
-> Agent Memory generic external-evidence normalization
```

cMCP remains an optional independent peer. It does not become a required Agent Memory runtime or policy store.

## Exact peer pin

```text
repository: agentrust-io/cmcp
release: v0.4.0
source commit: a2e95151356c9ae6c545330c900f3d4af0e447c1
runtime package: cmcp-runtime==0.4.0
TRACE package: agentrust-trace==0.9.0
Agent Manifest package: agent-manifest==0.11.2
```

The v0.4.0 pin matters semantically. That release tightened attestation verification after earlier versions could over-report assurance for incomplete or forged TPM evidence.

## One peer claim, two evidence records

A cMCP GatewayClaim contains several different kinds of evidence. V0.1 deliberately refuses to collapse them into a single boolean.

```text
signed gateway/session claim
+ approved policy bundle binding
+ audit-chain structure
+ enforcement mode
+ runtime measurement / attestation posture
+ optional agent identity
```

The adapter emits at least two independent Agent Memory candidates.

### Enforcement / configuration evidence

The enforcement record preserves bounded facts such as:

- gateway/session subject;
- cMCP release and verifier identity;
- exact signed-claim digest;
- approved policy bundle ref/hash;
- tool-catalog configuration ref;
- audit-chain root/tip refs;
- `enforce`, `advisory`, or `silent` posture;
- runtime ref;
- freshness;
- optional Agent Manifest ref.

A claim may establish this integrity/configuration posture when the released verifier checks the relevant fields even if hardware attestation remains unverified.

### Runtime attestation evidence

The attestation record separately preserves:

- runtime platform;
- runtime measurement ref;
- attestation verification posture;
- generated-at and validity window;
- hardware-verified versus software-only/unverified state;
- the same source-claim digest and bounded evidence refs.

A software-only claim therefore remains explicitly non-hardware-backed. It cannot inherit the verification status of the policy or audit fields merely because they occur in the same signed envelope.

## Claim-scoped verification

cMCP's verifier exposes a global status plus `verified_fields` and `unverified_fields`.

Agent Memory consumes the field-level evidence rather than copying the global label blindly.

For enforcement/configuration evidence, V0.1 requires:

```text
schema
signature
policy_bundle.hash
tool_catalog.hash
audit_chain
+
(public_key_binding OR externally trusted_public_key)
```

Security-critical failures such as signature, signer binding, policy/catalog hash, audit-chain, claim-shape, or requested Agent Manifest binding failure make the enforcement evidence invalid.

Hardware-attestation failure is evaluated separately when the enforcement signer/configuration evidence remains independently bound.

For attestation evidence:

```text
hardware_attestation in verified_fields -> verified
software-only / absent hardware proof    -> unknown
hardware/key-binding verification failure -> failed
```

Freshness is still evaluated independently by the generic Agent Memory normalizer.

## Core boundaries

```text
configured policy != enforcing posture
enforcing posture != action execution
audit-chain integrity != lifecycle satisfaction
hardware attestation != semantic correctness
verified gateway identity != Agent Memory authority
policy allow != approval
software-only verification != hardware provenance
```

These remain true even when every cryptographic check available to the peer passes.

## Privacy and minimization

The normalized records use refs and digests rather than copying cMCP's rich payloads.

V0.1 does not retain:

- raw tool arguments or responses;
- tool transcript entries;
- prompts or Agent Memory content;
- raw TEE/TPM evidence;
- quote signatures;
- certificate chains;
- complete Agent Manifest payloads.

The full cMCP claim may be held by the external evidence custodian, while Agent Memory records the stable digest and bounded provenance needed to reconstruct where the evidence came from.

## Failure semantics

### Software-only

A real released software-only cMCP claim may verify its schema, signature, pinned signer, policy/catalog hashes, freshness, and audit-chain structure while the global result remains `partially_verified` because hardware attestation is absent.

Agent Memory therefore permits:

```text
enforcement/configuration evidence = verified
attestation evidence = unknown
```

when those exact field-level conditions hold.

### Stale attestation

Expired evidence remains historical evidence but is not current applicability.

### Policy/catalog/signature mismatch

A failed signed-policy/configuration binding invalidates the enforcement evidence. It is not softened merely because another field in the same peer claim verified.

### Hardware evidence supplied but invalid

Hardware-attestation failure remains failed evidence. It must not degrade to a successful hardware claim.

### Missing hardware evidence

Absence of hardware proof must remain visibly unverified/unknown rather than being upgraded by the existence of a signed software claim.

## Relationship to execution evidence

cMCP may operate in an enforcing mode, but a GatewayClaim's declared enforcement posture is not itself an Agent Memory execution witness.

```text
enforcement_mode = enforce
!=
this specific Agent Memory action executed or was prevented
```

Execution claims continue to require the separate execution/evidence contracts already defined by Agent Memory.

## V0.1 evidence target

The dedicated exact-head comparator uses the real released cMCP claim builder and verifier to exercise:

- `enforce`, `advisory`, and `silent` modes;
- software-only partial verification without hardware overclaim;
- stale attestation;
- wrong approved policy hash;
- tampered claim signature;
- privacy minimization of attestation payloads.

Synthetic unit tests separately mutation-test claim-scoped classification and unknown-field minimization without making cMCP a core dependency.

## Non-goals

- claiming production cMCP deployment;
- provisioning real TPM, SNP, or TDX hardware in CI;
- making cMCP a required Agent Memory gateway;
- importing cMCP claim schema as Agent Memory doctrine;
- treating cMCP policy as canonical Agent Memory policy;
- treating an Agent Manifest binding as PAMA authority;
- storing raw audit, tool, identity, or attestation payloads;
- implementing Cedarling or another policy peer in this slice.
