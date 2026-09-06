# Privacy-Safe Runtime Trace Correlation Profile

Status: reference V0.1 implementation profile for issue #185.

## Purpose

This profile correlates Agent Memory governance/evidence artifacts with distributed runtime traces while minimizing exported state and preserving evidence boundaries.

```text
trace correlation != memory authority
span success != semantic correctness
span completion != lifecycle satisfaction
sampled telemetry != complete execution evidence
```

The correlation record is a linkage surface. It is not a replacement for PAMA decision receipts, decision-composition receipts, execution witnesses, or lifecycle evidence.

## External reference pin

V0.1 documentation/fixtures use OpenTelemetry Semantic Conventions **v1.42.0** as the pinned external reference point.

The actual Agent Memory profile does not import OpenTelemetry semantic-convention vocabulary as canonical memory semantics and does not require an OpenTelemetry SDK dependency.

The stable trace identity concepts used here are:

```text
TraceId: 16 bytes / 32 hexadecimal characters
SpanId:   8 bytes / 16 hexadecimal characters
```

The V0.1 serialized profile requires lowercase hexadecimal and rejects all-zero identifiers.

## Layering

```text
runtime / OpenTelemetry adapter
  -> trace/span IDs + minimized runtime references
  -> vendor-neutral Agent Memory trace correlation
  -> optional exporter / collector / evidence consumer
```

Peer/runtime-specific attributes remain outside canonical Agent Memory semantics.

## Normalized record

Schema:

`schemas/runtime-trace-correlation.schema.json`

Reference implementation:

`reference/agentmem_ref/memory/runtime_trace_correlation.py`

The bounded record can carry:

- telemetry observation state;
- sampling state;
- trace/span/parent-span identity when observed;
- runtime and optional service references;
- Agent Memory action reference;
- exact input identity when available;
- PAMA decision reference;
- decision composition reference;
- execution-witness reference;
- external evidence references;
- policy references;
- opaque scope, tenant, and project references;
- correlation timestamp.

It does not require raw memory content or complete trace payloads.

## Telemetry state and sampling are separate

Telemetry state:

```text
observed
not_observed
telemetry_unavailable
```

Sampling state:

```text
sampled
not_sampled
unknown
```

A record can therefore say that telemetry was observed while sampling configuration remains unknown. Likewise, `not_observed` does not become a claim that the underlying action did not execute.

For `not_observed` or `telemetry_unavailable`, V0.1 prohibits trace/span IDs in the normalized record so absence semantics cannot be mixed with purported trace identity.

## Binding

Observed telemetry is compared against the expected Agent Memory context using available exact dimensions:

```text
action_ref
input_identity
scope_ref
tenant_ref
project_ref
```

The result is:

```text
exact
mismatch
not_evaluated
```

Missing or mismatched required context is preserved in `binding_reasons`, for example:

```text
action_ref_mismatch
input_identity_mismatch
scope_ref_mismatch
tenant_ref_mismatch
project_ref_mismatch
```

No timing heuristic, span name, semantic similarity, or model inference may turn a mismatch into an exact correlation in V0.1.

## Privacy and minimization

The normalizer accepts an adapter result but emits only a fixed whitelist of correlation metadata.

Unknown adapter fields are discarded. The executable test suite explicitly injects and rejects persistence of fields such as:

- `memory_content`;
- `prompt`;
- `system_instructions`;
- `tool_request_payload`;
- `hidden_reasoning`.

Full decision receipts and raw tool/model payloads are not required by this profile.

Opaque references should be preferred over tenant/project display names where they are sufficient for correlation.

## Authority and evidence non-claims

Every normalized record fixes:

```text
authority_effect = none
execution_claim = not_established
lifecycle_satisfaction = not_established
```

Even when an `execution_witness_ref` is present, the trace correlation itself does not duplicate or upgrade the witness claim. It simply links to the independent evidence surface introduced by #152 Phase 3.

This prevents a successful span or completed trace from silently becoming proof that:

- PAMA authorized a memory consequence;
- a downstream action definitely executed;
- deletion/correction/forgetting obligations were satisfied.

## Adversarial evidence

Fixture:

`fixtures/runtime-trace-correlation-matrix.json`

Tests:

`reference/tests/test_runtime_trace_correlation.py`

The bounded V0.1 set covers:

- sampled exact trace correlation;
- exact correlation with unknown sampling state;
- wrong action identity;
- wrong Agent Memory input identity;
- cross-scope/tenant/project mismatch;
- telemetry not observed;
- telemetry unavailable;
- all-zero TraceId rejection;
- all-zero SpanId rejection;
- raw sensitive adapter fields being discarded;
- execution witness remaining an independent reference;
- prohibition on attaching trace IDs to an unobserved telemetry state.

## Removal / rollback

The adapter and correlation surface are optional.

Removing an OpenTelemetry/runtime adapter does not alter canonical memory records, PAMA decisions, lifecycle state, or execution-witness evidence. Existing normalized correlation records remain understandable from their vendor-neutral schema and references.

## What V0.1 proves

Within the bounded fixtures/tests, V0.1 demonstrates that:

- runtime trace identity can be correlated without copying memory content;
- TraceId and SpanId shape/non-zero rules are deterministic;
- exact Agent Memory action/input/scope binding remains visible;
- cross-scope evidence cannot silently become exact correlation;
- telemetry absence remains absence, not non-execution proof;
- unknown sampling remains unknown;
- trace correlation does not create authority or lifecycle claims;
- no OpenTelemetry SDK is required for the core/reference contract.

## What V0.1 does not prove

This slice does not prove:

- production collector/exporter availability;
- complete trace capture;
- correctness of a framework's instrumentation;
- execution merely because a span completed;
- non-execution because no telemetry was observed;
- semantic correctness of runtime behavior;
- lifecycle obligation satisfaction;
- compatibility with every OpenTelemetry semantic-convention version;
- a need for new upstream OpenTelemetry semantic conventions.
