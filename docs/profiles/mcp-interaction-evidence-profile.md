# Governed MCP Interaction Evidence Profile

Status: V0.1 reference profile for #190.

This profile defines the minimum Agent Memory-facing evidence seam for Model Context Protocol (MCP) tool and resource interactions. MCP is a runtime/wire protocol input, not Agent Memory authority, memory admission, execution proof, or lifecycle doctrine.

The V0.1 reference is pinned to:

- Model Context Protocol stable revision `2026-07-28`
- repository `modelcontextprotocol/modelcontextprotocol`
- source commit `5f5440bb26a62e2cf3440b92da5a667efa03b267`

The exact source revision is evidence metadata. MCP remains optional and replaceable.

## Core boundary

```text
MCP transport success
!= Agent Memory authorization

MCP server identity
!= memory authority

MCP tool result
!= execution witness
!= durable memory

MCP resource content
!= admitted memory

MCP interaction evidence
!= lifecycle satisfaction
```

A successful MCP exchange proves only what the observed protocol evidence actually supports.

## V0.1 protocol surface

V0.1 covers exactly two MCP interactions:

```text
tools/call
resources/read
```

The pinned specification defines `tools/call` as a JSON-RPC request to invoke a server-exposed tool and `resources/read` as a JSON-RPC request to retrieve resource contents.

The profile does not reproduce complete MCP requests or results. It preserves the minimum evidence needed to correlate an interaction with Agent Memory governance and scope.

## Why request ID is not authority

MCP uses JSON-RPC request IDs to correlate requests and responses. The pinned tool specification also requires a new JSON-RPC request ID when a `tools/call` interaction continues after an `input_required` result.

Therefore:

```text
same logical activity
may use multiple MCP request IDs

request ID
= correlation evidence
!= action identity
!= approval
!= authority token
```

Agent Memory durable-mutation identity remains bound through `action_ref`, `input_identity`, and scope rather than through MCP request ID reuse.

## Why server and tool names are not global identity

The pinned MCP tool specification states that tool-name uniqueness is scoped to a single server. It also notes that the server `name` from `serverInfo` is not guaranteed globally unique and should not be relied upon for disambiguation.

V0.1 therefore requires an adapter-supplied stable `server_ref` and a server-scoped `target_ref`.

For example:

```text
server_ref = mcp-server:memory-tools-a
target_ref = mcp-tool:mcp-server:memory-tools-a:memory.update
```

These are correlation references, not memory authority.

## Generic evidence envelope

The normalized evidence surface preserves:

```text
MCP revision / exact source commit
client / server opaque refs
session / transport refs when available
JSON-RPC request id
interaction kind and method
server-scoped tool/resource target ref
memory effect classification
request observed state
result observed state and classification
request / result digests
Agent Memory action / input identity when applicable
scope / tenant / project refs
PAMA / composition / approval / execution refs when available
runtime trace-correlation ref when available
bounded evidence refs
```

Unknown peer fields are discarded.

## Memory effect classification

Each interaction is classified as one of:

- `none`: no Agent Memory admission or durable-mutation path is being proposed;
- `memory_candidate`: MCP content may be offered to normal Agent Memory admission later;
- `durable_mutation`: the interaction may participate in a durable Agent Memory mutation and therefore requires governed identity/scope binding.

`memory_candidate` is not admission.

```text
resource/tool output
-> evidence or candidate
-> normal Agent Memory admission/governance

resource/tool output
!= canonical memory
```

## Exact durable-mutation binding

A `durable_mutation` interaction must bind to at least:

```text
action_ref
input_identity
scope_ref
```

Expected tenant/project bindings are compared when provided.

Missing or mismatched binding is explicit:

```text
binding_status = mismatch
governance_alignment = binding_mismatch
```

Timing, request ID, tool name, result similarity, or server display identity must not repair an identity mismatch.

## Governance availability and monotonicity

For a durable mutation, governance may be `available` or `unavailable`. It may not be declared `not_required`.

When governance is unavailable:

```text
governance_alignment = blocked_governance_unavailable
```

The protocol adapter does not infer permission from MCP transport or tool success.

When a stricter Agent Memory composition says `deny`, an observed successful MCP result is recorded as:

```text
result_classification = success
effective_decision = deny
governance_alignment = result_observed_under_deny
```

That is conflict/incident evidence. It is not retroactive authorization.

When the effective decision is `require_approval`, MCP `input_required`, user interaction, or a successful result does not prove approval satisfaction. Approval remains the exact-identity approval-evidence boundary defined separately by Agent Memory.

## Result states

V0.1 keeps protocol observation separate from interpretation:

```text
result_status:
  complete
  input_required
  mcp_error
  unavailable
  not_observed

result_classification:
  success
  tool_error
  protocol_error
  input_required
  unavailable
  not_observed
```

Observed result-like states carry a digest. Unavailable or unobserved results do not fabricate one.

An MCP protocol error may preserve the integer JSON-RPC error code as bounded evidence.

## Execution evidence remains separate

MCP result evidence is not an Agent Memory execution witness.

```text
MCP request/result observed
!= enforcement point observed
!= action execution verified
```

When an Agent Memory `execution_witness_ref` exists, V0.1 may correlate it. When it does not, the profile preserves:

```text
execution_claim = not_established
```

Missing trace correlation is handled the same way. It is an evidence gap, not proof of non-execution.

## Resource reads

The pinned MCP resource specification defines `resources/read` as retrieval of resource contents identified by URI. Resources can contain text or binary data and may return multiple content items.

Agent Memory does not need those bodies in its durable protocol evidence record.

V0.1 preserves a stable `target_ref`, request/result digests, result classification, and bounded provenance references. Content may separately enter normal evidence/admission processing if policy requires it.

## Privacy and minimization

Default posture:

```text
refs / IDs / digests / classifications first
raw payloads only in a separately governed system when actually required
```

The normalized V0.1 record does not require or copy:

- raw prompts or system instructions;
- complete tool arguments;
- complete tool result payloads;
- resource bodies;
- hidden reasoning;
- access tokens, authorization headers, credentials, or secrets;
- server/client runtime objects;
- tenant/project display names when opaque refs suffice.

The pinned MCP tool specification separately warns against exposing sensitive parameters through transport headers. Agent Memory does not treat transport metadata as a safe durable-content channel.

## Required negative paths

The executable V0.1 matrix covers:

1. successful MCP tool result after Agent Memory `deny` remains conflict evidence, not authorization;
2. resource-read content is not automatically admitted durable memory;
3. wrong Agent Memory input identity produces a binding mismatch;
4. the same request/tool identity in another tenant/project does not correlate across scope;
5. server/governance unavailability remains explicit and cannot widen durable-mutation authority;
6. peer-supplied PAMA/lifecycle/permission fields are discarded;
7. missing trace/execution witness remains an explicit evidence gap rather than non-execution proof;
8. removing the MCP adapter leaves canonical Agent Memory records interpretable through generic refs/digests/governance evidence.

Additional tests cover exact spec pinning, method/kind mismatch, protocol errors, `input_required`, deterministic normalization, and payload minimization.

## Deployment profiles

V0.1 supports these assumptions:

### L: local / single-user

- stdio or local MCP server use is allowed;
- no enterprise identity provider is required;
- governance evidence may remain local;
- raw payload retention is not required.

### T: team / multi-tenant

- explicit tenant/project binding is supported;
- same tool/request identifiers cannot cross-correlate by similarity;
- opaque references are preferred over display names.

### E: enterprise governed estate

- external PAMA/composition/approval/execution references may be correlated;
- gateway/transport success cannot widen Agent Memory authority;
- unavailability remains explicit.

### H: high assurance

- exact MCP revision and source commit are reconstructable;
- durable-mutation identity binding is deterministic;
- evidence gaps and non-claims remain explicit;
- request/result payloads are represented by digests rather than copied by default.

Cross-organization delegated authority is not a V0.1 target.

## V0.1 non-claims

V0.1 does not claim:

- an MCP server is Agent Memory-conformant;
- MCP authentication or server identity grants PAMA authority;
- a successful tool call proves authorized execution;
- MCP resource content is durable memory;
- an MCP request ID is a durable action identity;
- `input_required` is approval evidence;
- MCP tool annotations are trusted governance input;
- trace absence proves an action did not occur;
- protocol evidence satisfies Agent Memory lifecycle obligations;
- MCP is required for Agent Memory implementations.

## Rollback / removal

The MCP adapter/profile is optional. Removing it leaves canonical Agent Memory state and governance receipts interpretable because the normalized record references Agent Memory identities and receipts instead of embedding MCP runtime objects or making MCP identifiers canonical memory authority.

## Stop line

Do not expand V0.1 into:

- an MCP client or server framework;
- arbitrary MCP method coverage;
- A2A/cross-agent delegation;
- upstream MCP protocol extensions;
- MCP authentication as PAMA authority;
- raw payload persistence;
- claims that MCP execution evidence proves lifecycle satisfaction.

A2A belongs in a separate implementation slice after the MCP boundary is stable.
