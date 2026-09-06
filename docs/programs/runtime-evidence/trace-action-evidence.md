# P4.5c TRACE-compatible external action evidence

Status: **Executable interoperability evidence**. This slice maps P4.5a portable Agent Memory governance evidence into the existing AgenTrust external action-evidence surface without making TRACE or cMCP responsible for PAMA, isolation-domain membership, or memory lifecycle semantics.

Parent implementation issue: #63.

## Pinned external surfaces

The executable/reference surfaces are pinned to:

```text
TRACE SDK:        agentrust-trace==0.9.0
TRACE release:    94271a1630601c94e80a23263d9750cb8d39f1f4
cMCP runtime:     cmcp-runtime==0.4.0
cMCP release:     a2e95151356c9ae6c545330c900f3d4af0e447c1
RFC 8785 library: rfc8785==0.1.4
```

Relevant upstream contracts:

- [TRACE action-receipt verification guidance](https://github.com/agentrust-io/trace-spec/blob/94271a1630601c94e80a23263d9750cb8d39f1f4/docs/verification.md)
- [TRACE action-receipt planning](https://github.com/agentrust-io/trace-spec/issues/66)
- [TRACE external execution evidence guidance](https://github.com/agentrust-io/trace-spec/issues/34)
- [cMCP external execution evidence schema](https://github.com/agentrust-io/cmcp/blob/a2e95151356c9ae6c545330c900f3d4af0e447c1/schemas/audit-entry.schema.json)
- [cMCP released verifier implementation](https://github.com/agentrust-io/cmcp/blob/a2e95151356c9ae6c545330c900f3d4af0e447c1/src/cmcp_verify/verify.py)
- [cMCP embodied action evidence profile](https://github.com/agentrust-io/cmcp/blob/a2e95151356c9ae6c545330c900f3d4af0e447c1/docs/spec/embodied-action-evidence.md)
- [AgenTrust integration front door](https://github.com/agentrust-io/integrations/tree/main/integrations)

The released packages are comparators and interoperability dependencies for this reference slice. They do not become Agent Memory doctrine.

## Ownership boundary

The evidence chain is:

```text
Agent Memory canonical receipt
        |
        | P4.5a content-free signed projection
        v
portable Agent Memory governance evidence
        |
        | content-addressed reference + action_ref
        v
P4.5c detached action payload
        |
        | evidence_hash
        v
cMCP external_execution_evidence envelope
        |
        | linked_call_id + issuer signature
        v
TRACE/cMCP action-receipt verification
```

The meanings remain separate:

```text
TRACE/cMCP receipt integrity != PAMA permission
TRACE/cMCP receipt integrity != isolation-domain membership
external accepted outcome    != lifecycle satisfaction
external rejected outcome    != malformed evidence
valid action evidence         != physical completion
```

Agent Memory remains authoritative for memory-action meaning, PAMA, canonical receipt semantics, isolation-domain meaning and membership continuity, correction/deletion obligations, residue, and lifecycle satisfaction.

## Existing envelope, no new TRACE wire format

P4.5c uses the existing six-field cMCP `external_execution_evidence` envelope exactly:

```json
{
  "issuer": "spiffe://runtime.example/agent-memory-controller",
  "issuer_key_id": "<sha256 raw Ed25519 public key hex>",
  "signature": "<base64url Ed25519 signature>",
  "evidence_hash": "sha256:<detached payload hash>",
  "evidence_type": "opaque-receipt",
  "linked_call_id": "<audit call_id>"
}
```

`opaque-receipt` is deliberate. Agent Memory evidence is not itself a controller-native receipt, a TEE attestation, or a JWT. Reusing an existing generic envelope value is more accurate than proposing a new normative TRACE evidence type before implementation exposes a generic need.

`linked_call_id` remains the audit-chain identifier. It is not overloaded with Agent Memory `action_ref`.

## Detached payload

Schema: `../../../schemas/trace-action-evidence-bundle.schema.json`.

The detached payload is content-free:

```json
{
  "profile": "agent-memory.trace-action-evidence.v1",
  "call_id": "<audit call_id>",
  "action_ref": "<signed Agent Memory runtime action reference>",
  "portable_evidence_ref": "sha256:<P4.5a evidence reference>",
  "canonical_receipt_ref": "sha256:<Agent Memory receipt reference>",
  "execution_outcome": "accepted | rejected",
  "execution_time": "2026-08-11T21:00:03Z",
  "source_domain_ref": "<optional opaque reference>",
  "destination_domain_ref": "<optional opaque reference>",
  "domain_authorization_state_ref": "<optional opaque membership/authorization-state reference>"
}
```

It intentionally excludes:

- raw memory content;
- hidden reasoning;
- full canonical receipts;
- PAMA policy contents;
- tenant/project/domain display names when opaque references suffice;
- a claim that TRACE understands Agent Memory authority or lifecycle semantics.

## Two canonicalization domains

The upstream contracts currently use two serialization rules, and P4.5c preserves both.

The detached payload uses **RFC 8785/JCS**, matching TRACE/cMCP action-evidence guidance:

```text
evidence_hash = sha256(JCS(detached_payload))
```

The cMCP released verifier signs the six-field envelope using compact, key-sorted JSON with `ensure_ascii=True`, excluding only `signature` from the signing input.

P4.5c reproduces that verifier behavior exactly for the envelope. It does not silently substitute JCS and claim wire compatibility where the released verifier has a different pre-image.

## Replay and binding model

P4.5c deliberately checks both identifiers:

```text
linked_call_id -> audit-chain call identity
action_ref     -> Agent Memory runtime action identity
```

A receipt replayed onto another call fails `linked_call_id` binding. A receipt correlated to the wrong Agent Memory action fails `action_ref` binding even if the call identifier is unchanged.

The verifier also binds:

- detached payload hash to the signed external envelope;
- detached `portable_evidence_ref` to the supplied P4.5a evidence;
- detached `canonical_receipt_ref` to the signed P4.5a receipt reference;
- optional source/destination opaque domain references to the P4.5a scope;
- optional opaque `domain_authorization_state_ref` to the P4.5a scope;
- external execution time to the P4.5a decision-time ordering check.

No external receipt is allowed to manufacture execution-time PAMA authority or isolation-domain membership. Those continuity facts remain Agent Memory verifier inputs rather than TRACE semantics.

## Domain-authorization non-escalation

A valid TRACE/cMCP receipt proves the configured action-evidence binding. It does not prove that the Agent Memory actor still held permission to cross a memory-domain boundary at execution time.

For a signed cross-domain consequence, Agent Memory independently evaluates:

```text
source_domain_ref
destination_domain_ref
domain_authorization_state_ref
domain_authorization_valid_at_execution
```

The executable paths distinguish:

```text
TRACE receipt = valid accepted
Agent Memory evidence = valid
domain membership at execution = valid
runtime execution = executed_as_authorized
```

from:

```text
TRACE receipt = valid accepted
Agent Memory evidence = valid
domain membership at execution = revoked/expired
runtime execution = unauthorized_execution
```

and from:

```text
TRACE receipt = valid accepted
Agent Memory evidence = valid
required domain-continuity evidence = missing
runtime execution = unverifiable
```

This is intentional. Historical receipt authenticity does not need to be rewritten when authorization changes. The runtime result carries the current execution-time authority truth.

## TRACE result taxonomy

The local adapter follows the action-receipt states documented by TRACE:

```text
receipt_valid_accepted
receipt_valid_rejected
receipt_missing_required
receipt_invalid
receipt_unverified
```

A valid rejection is first-class negative evidence. It does not make the receipt malformed.

Unknown issuer trust is reported locally as `receipt_unverified` when every non-cryptographic binding is otherwise sound. This matches TRACE guidance for an unpinned optional issuer.

The released cMCP `verify_audit_bundle()` comparator is stricter once `external_evidence_keys` verification is enabled: an envelope whose `issuer_key_id` is absent from the supplied trusted-key map fails the bundle verification. P4.5c executes and records both behaviors instead of pretending the policy choices are identical.

## Lifecycle non-escalation

P4.5c executes an externally accepted action receipt with both:

```text
Agent Memory lifecycle = residual
```

and:

```text
Agent Memory lifecycle = satisfied
```

Both TRACE bindings remain valid. The lifecycle difference comes from Agent Memory evidence.

It also executes a valid external `rejected` outcome while retaining the Agent Memory governance and lifecycle dimensions separately. This demonstrates that a downstream negative outcome is evidence, not a signature failure.

## Real upstream comparator

`../../../reference/run_trace_cmcp_comparator.py` runs in a dedicated virtual environment and calls the released:

```python
cmcp_verify.verify_audit_bundle()
```

against the P4.5c envelope.

The comparator proves that the real upstream verifier:

- accepts the correctly signed P4.5c envelope;
- rejects replay to a different `linked_call_id`;
- rejects signature tampering;
- fails closed when its configured external issuer trust map does not contain the receipt key.

The isolated environment is intentional because the current cMCP/AGT dependency line resolves a cryptography version below the repository's P4.5a `cryptography==50.0.0` validation pin. Comparator isolation avoids weakening the primary evidence environment merely to make dependency resolvers happier.

## Executed local vectors

`../../../reference/tests/test_trace_action_evidence.py` covers:

- exact TRACE and cMCP release identities;
- accepted external receipt plus lifecycle `residual`;
- accepted external receipt plus lifecycle `satisfied`;
- valid external rejection as negative evidence;
- valid TRACE receipt plus revoked Agent Memory domain membership;
- wrong `linked_call_id` replay;
- wrong Agent Memory `action_ref` replay;
- detached payload tampering;
- external envelope signature tampering;
- unknown/untrusted external issuer;
- missing required receipt;
- isolation-domain mismatch;
- domain-authorization-state mismatch;
- schema validation;
- absence of raw memory content;
- exact reuse of the existing six-field cMCP envelope.

Run the local profile:

```bash
python -m pip install \
  jsonschema==4.26.0 \
  cryptography==50.0.0 \
  agent-manifest==0.11.2 \
  agentrust-trace==0.9.0 \
  rfc8785==0.1.4
python -m unittest discover -s reference/tests -t reference
python scripts/validate_schemas.py
```

Run the isolated upstream comparator:

```bash
python -m venv /tmp/agent-memory-p45c-cmcp
/tmp/agent-memory-p45c-cmcp/bin/python -m pip install \
  cmcp-runtime==0.4.0 \
  agentrust-trace==0.9.0 \
  agent-manifest==0.11.2 \
  rfc8785==0.1.4
PYTHONPATH=reference \
  /tmp/agent-memory-p45c-cmcp/bin/python reference/run_trace_cmcp_comparator.py
```

## Upstream contribution surface

The implementation evidence supports an upstream integration contribution under the existing AgenTrust integration front door, preferably:

```text
agentrust-io/integrations/
  integrations/agent-memory/
```

The initial target should be a Community integration containing the technical README, reproducible vectors, explicit claim boundaries, and a pointer to the verifier/adapter implementation.

P4.5c does **not** justify a normative TRACE schema proposal. The current external execution evidence envelope is sufficient for this implementation. A core-spec change should be proposed only if later integration work exposes a generic requirement that cannot be represented without one.

## What this slice proves

P4.5c demonstrates that P4.5a Agent Memory governance evidence can be bound to an existing TRACE/cMCP action-evidence path, checked for both call and action replay, verified by the released cMCP implementation, and interpreted without TRACE implementing PAMA or receiving raw memory.

The evidence remains multi-dimensional:

```text
valid TRACE receipt + committed Agent Memory decision + lifecycle residual
valid TRACE receipt + committed Agent Memory decision + lifecycle satisfied
valid TRACE rejection + independently valid Agent Memory governance evidence
valid TRACE receipt + revoked Agent Memory domain membership + unauthorized execution
```

## What remains unproven

This slice does not prove:

- TRACE Trust Record hardware attestation of an Agent Memory process;
- physical completion or functional-safety certification;
- production issuer-key discovery or revocation infrastructure;
- production isolation-domain membership discovery/revocation infrastructure;
- upstream Community/Verified integration acceptance;
- generic cross-organization trust-anchor discovery;
- AGT/runtime-policy composition (optional P4.5d);
- any Agent Memory conformance-level increase;
- acceptance of ADR-020, ADR-021, or ADR-022.

Those remain separate evidence and governance decisions.
