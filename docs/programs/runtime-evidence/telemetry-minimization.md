# P8 Telemetry Interoperability Without Shadow Memory

## Purpose

Make Agent Memory operationally observable without copying governed memory into a less-governed telemetry backend.

Canonical audit events remain the reconstructable evidence surface. Telemetry is a deliberately lossy derived projection used for correlation, health, and operational analysis.

The governing risk is **shadow memory**: raw memory content, prompts, summaries, evidence payloads, identities, or authority context copied into logs/traces/metrics where retention, access, deletion, and lifecycle controls are weaker than the memory system they observe.

## V1 minimization profile

`reference/agentmem_ref/memory/telemetry.py` projects schema-valid `memory-audit-event` records into `telemetry-projection.schema.json`.

The projection is strict allowlist, not denylist.

Allowed directly:

- event family and event schema version;
- component name;
- timestamp;
- booleans indicating whether payload, signal, or authority context existed;
- count of sensitivity labels, without the labels themselves.

Potentially identifying or cross-linkable values are emitted only as keyed HMAC-SHA256 references:

- event id;
- memory id;
- actor;
- principal;
- correlation and causation ids;
- policy version;
- receipt and ledger references.

The HMAC key is local configuration and is not emitted. Different telemetry domains may use different keys so opaque identifiers do not automatically become globally linkable pseudonyms.

Each projection also carries a non-secret `key_id` identifying the HMAC key generation. The identifier exists for retention/deletion accounting and is not an authority or trust signal.

Explicitly absent from the projection:

- `payload` contents;
- memory text or prompt content;
- raw actor/principal/memory identifiers;
- raw sensitivity labels;
- signal values and uncertainty bodies;
- estimator details;
- authority refs;
- permitted/prohibited/selected action names;
- raw receipt or ledger identifiers.

## V2 retention and deletion

`reference/agentmem_ref/memory/telemetry_retention.py` treats minimized telemetry as governed derived state rather than an indefinite logging exemption.

The local reference store persists only:

- the validated telemetry projection;
- an expiry timestamp.

It does **not** persist the raw memory id or HMAC key used to create the projection.

### Expiry

Every stored projection has an explicit `expires_at`. `purge_expired()` removes records whose retention window has ended without needing to recover any source memory content.

### Memory-targeted purge

For deletion obligations, the raw memory id is supplied transiently to `purge_memory()`. The store receives the currently retained telemetry projectors, indexed by `key_id`, and recomputes the target's opaque `am.memory_ref` under each available HMAC key generation.

This supports key rotation without making older telemetry unreachable for deletion:

```text
raw memory id
  -> ref under telemetry-2026-07
  -> ref under telemetry-2026-08
  -> ...
  -> purge every matching retained projection
```

The raw memory id and HMAC keys are not added to telemetry storage as a side effect of deletion.

### Missing key generations fail closed

If retained telemetry contains a `key_id` for which the deletion process no longer has the HMAC key, those records cannot be tested for membership in the target memory's telemetry closure.

The result is therefore:

```text
unresolved key generation -> purge complete = false
```

Losing a pseudonymization key is not treated as proof that old telemetry no longer represents the deleted memory.

This is intentionally conservative. Operators may later satisfy the obligation through expiry, deletion of the unresolved telemetry partition, restored key custody, or other independently verified remediation. The local reference does not invent a success verdict.

## Semantics

```text
canonical audit event  -> authoritative reconstruction evidence
telemetry projection   -> minimized operational correlation only
telemetry purge         -> deletion of that derived observability state only
```

A valid telemetry span does not prove a memory mutation was authorized, correct, complete, or successfully forgotten. Likewise, a successful telemetry purge does not by itself prove canonical memory forgetting completeness. It closes only the telemetry portion of the derived-state obligation.

Telemetry retention must be governed independently. Pseudonymization reduces disclosure risk but does not make telemetry anonymous, non-sensitive, or exempt from retention/deletion policy.

## Interoperability posture

The V1/V2 shape uses primitive span-style attributes that can be mapped into common observability systems, but these slices do not claim formal OpenTelemetry semantic-convention adoption or require an external telemetry SDK.

That separation is intentional. Agent Memory defines the privacy/governance contract first. A later adapter may map this content-free shape into a specific telemetry transport without weakening it.

## Validation

`reference/tests/test_telemetry.py` injects a canonical audit event containing deliberately sensitive prompt/memory payloads, credential-like content, raw identities, sensitivity labels, signal/uncertainty details, authority/action names, and receipt/ledger ids. The serialized projection must contain none of those raw values.

`reference/tests/test_telemetry_retention.py` verifies:

- targeted purge removes only the requested memory's telemetry;
- one memory emitted under multiple HMAC key generations is purged across all known generations;
- a missing retired key generation makes the result explicitly incomplete;
- expiry removes records without source-memory lookup;
- stored telemetry contains neither raw memory identifiers nor HMAC key material.

## Claim boundary

P8 V1/V2 demonstrate a local privacy-minimized telemetry seam and rotation-aware retention/deletion behavior. They do not claim:

- that telemetry is anonymous;
- that a production telemetry backend automatically satisfies these requirements;
- that telemetry replaces canonical receipts or audit events;
- formal compliance with any external observability standard;
- production collector/exporter behavior;
- that telemetry purge alone satisfies overall memory forgetting completeness;
- any upstream submission or external repository change.

## P8 posture

The core local P8 risk is now executable on both sides of the lifecycle: content is minimized before telemetry emission, and retained pseudonymous telemetry can expire or be targeted for deletion across known key rotations without converting missing keys into a false success claim.

Further production work may test a concrete collector/storage backend, but that is a deployment-specific evidence extension rather than a reason to weaken the local minimization and retention contract.
