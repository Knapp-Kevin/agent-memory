# Governed A2A Collaboration Evidence Profile

Status: V0.1 reference profile for #194.

This profile defines the minimum Agent Memory-facing evidence seam for Agent2Agent (A2A) collaboration while deliberately refusing authority-bearing cross-agent memory transfer.

The V0.1 reference is pinned to:

- repository `a2aproject/A2A`
- stable release `v1.0.1`
- source commit `3303592588e388e62e0f69f701af531d2f4e3991`
- normative protocol source `specification/a2a.proto`

A2A is a transport/task interoperability input, not Agent Memory authority or lifecycle doctrine.

## Core boundary

```text
A2A Agent Card
!= delegated authority

A2A peer identity
!= memory authority

A2A task acceptance or completion
!= permission to mutate Agent Memory

A2A Message / Artifact
!= admitted memory

A2A task completion
!= Agent Memory execution witness
!= lifecycle satisfaction

cross-agent context transfer
!= authority transfer
```

## Why A2A fits the Agent Memory boundary

The pinned A2A specification is designed for collaboration between independent, potentially opaque agent systems without requiring access to each other's internal memory, tools, or reasoning.

That is compatible with Agent Memory minimization:

```text
collaborate by exchanging bounded context/evidence
rather than exporting the memory substrate
```

V0.1 therefore treats A2A as a collaboration evidence plane around Agent Memory, not a shared canonical memory implementation.

## A2A protocol facts used by V0.1

The pinned normative model defines:

- `AgentCard` as discovery metadata describing a remote agent, capabilities, skills, endpoint, and authentication requirements;
- `Message` as a communication turn with a unique message ID and optional task/context association;
- `Task` as a server-generated unit of work with task ID, context ID, status, artifacts, and optional history;
- `Artifact` as a task-scoped output containing one or more content parts;
- task lifecycle states including `SUBMITTED`, `WORKING`, `COMPLETED`, `FAILED`, `CANCELED`, `INPUT_REQUIRED`, `REJECTED`, and `AUTH_REQUIRED`;
- multiple protocol bindings over a common canonical model.

These protocol identities are useful correlation evidence. They are not Agent Memory permission objects.

## V0.1 interaction surface

The normalized profile recognizes four bounded interaction kinds:

```text
task_request
task_status
message
artifact
```

Direction is explicit:

```text
outbound
inbound
```

A V0.1 `task_request` is outbound. A V0.1 artifact observation is inbound.

## Export classification

Every collaboration record uses one of:

- `explicit_non_memory`: protocol/task evidence that is not proposed as memory;
- `context_projection`: minimized Agent Memory-derived context exported for a governed collaboration;
- `memory_candidate`: inbound peer content that may be offered to normal Agent Memory admission later.

No V0.1 classification transfers Agent Memory mutation authority to a remote peer.

```text
context_projection
!= authority grant

memory_candidate
!= memory admission
```

## Agent Card and peer identity

Agent Cards and remote identity evidence can answer useful questions such as:

- which remote endpoint/capability description was used;
- which Agent Card version/digest was observed;
- which remote identity/attestation evidence was associated with the interaction.

They do not answer:

- whether peer output is true;
- whether the peer may mutate local durable memory;
- whether the peer inherits local PAMA authority;
- whether a task result should become canonical memory.

V0.1 therefore preserves stable remote-agent and Agent Card refs/digests while fixing:

```text
agent_card_authority = none
delegated_memory_authority = not_established
semantic_correctness = not_established
```

External identity/attestation evidence may be correlated through the existing external-evidence boundary. Verification remains evidence, not authority.

## Exact Agent Memory binding

Outbound `context_projection` records must bind to at least:

```text
action_ref
input_identity
scope_ref
```

Tenant/project references are compared when supplied.

The binding cannot be repaired by:

- matching task IDs;
- matching context IDs;
- matching Agent Card names or capabilities;
- timing proximity;
- semantic similarity;
- remote task success.

A mismatch is explicit:

```text
binding_status = mismatch
governance_alignment = binding_mismatch
```

Inbound A2A events may also be correlated to a known local governed action. That correlation remains separate from whether the inbound content is memory.

## Exported memory evidence currentness

When an outbound context projection depends on Agent Memory state, V0.1 records:

```text
current
historical
stale
revoked
unknown
```

Historical, stale, or revoked state may remain useful as provenance or historical context, but cannot masquerade as current authority:

```text
memory_evidence_status = stale | revoked | historical
-> governance_alignment = historical_only
-> delegated_memory_authority = not_established
```

Correction and revocation references may be preserved without copying the underlying memory graph.

## Local governance remains monotonic

For outbound Agent Memory-derived context, governance may be `available` or `unavailable`. It may not be declared `not_required`.

```text
governance unavailable
-> blocked_governance_unavailable
```

A2A transport does not infer permission.

If local Agent Memory governance says `deny` but an inbound task reports progress/completion anyway, record the contradiction:

```text
effective_decision = deny
task_state = completed | working | ...
governance_alignment = remote_result_under_deny
```

That is incident/conflict evidence, not retroactive authorization.

If local governance requires approval, A2A task acceptance, `INPUT_REQUIRED`, `AUTH_REQUIRED`, remote identity, or task completion does not establish the Agent Memory approval evidence:

```text
governance_alignment = approval_not_established
```

Approval remains a separately verified exact-action artifact.

## Task state is protocol state, not lifecycle satisfaction

A2A task states describe the remote collaboration lifecycle.

A completed A2A task can mean the remote agent reports its task complete. It does not prove that:

- a local enforcement point observed the intended consequence;
- a local durable memory mutation was authorized;
- a correction/revocation obligation was satisfied;
- Agent Memory lifecycle obligations completed.

V0.1 therefore fixes:

```text
task_completion_authority = none
execution_claim = not_established
lifecycle_satisfaction = not_established
```

When stronger execution/trace evidence exists, it may be correlated through existing refs. Missing trace evidence remains a gap, not proof of non-execution.

## Inbound messages and artifacts

A2A Messages and Artifacts may contain useful evidence or candidate information.

Their content enters Agent Memory only through normal admission:

```text
A2A Message / Artifact
-> bounded evidence or memory_candidate
-> provenance / scope / trust / PAMA / lifecycle processing

A2A Message / Artifact
!= canonical memory
```

Peer-supplied fields named `pama_outcome`, `permission`, `authority`, `lifecycle_state`, `standing_grant`, or similar are not canonical merely because they arrived in a structured peer payload.

The V0.1 normalizer uses a fixed allowlist and discards unknown peer fields.

## Privacy and minimization

The normalized collaboration record defaults to:

```text
stable refs
opaque scope IDs
digests
bounded task state
governance/evidence refs
correction/revocation refs
```

It does not require or copy:

- the full canonical memory graph;
- raw hidden reasoning or internal plans;
- system prompts;
- unrelated remembered state;
- full Message parts;
- full Artifact content;
- complete Agent Card documents after a stable digest/ref is available;
- credentials/authentication headers or tokens;
- tenant/project display names when opaque refs suffice.

This preserves A2A's opaque-agent design rather than defeating it by turning interoperability into state exfiltration.

## Required negative paths

The executable V0.1 matrix covers:

1. powerful Agent Card skills/capabilities do not establish Agent Memory authority;
2. completed remote task under local `deny` remains conflict evidence, not authorization;
3. hostile peer PAMA/lifecycle/standing-grant fields cannot mutate canonical state;
4. inbound Artifact content is a candidate, not automatic durable memory;
5. identical task/context identity across another tenant/project cannot cross-correlate;
6. valid remote identity evidence does not establish semantic correctness or memory authority;
7. stale/revoked outbound memory evidence remains historical-only;
8. missing trace/execution evidence remains an evidence gap, not negative proof;
9. peer or governance unavailability cannot widen authority;
10. adapter removal leaves canonical Agent Memory state interpretable.

Additional tests cover exact release pinning, direction/kind constraints, approval non-equivalence, deterministic normalization, and raw-content minimization.

## Deployment profiles

### L: local / single-user

- local A2A peers may collaborate without enterprise identity infrastructure;
- opaque refs/digests remain sufficient for protocol evidence;
- full memory export is not required.

### T: team / multi-tenant

- tenant/project binding is explicit;
- peer task/context IDs do not bypass isolation;
- inbound candidates remain scoped before admission.

### E: enterprise governed estate

- external peer identity/attestation evidence may be correlated;
- local PAMA/composition/approval outcomes remain authoritative for Agent Memory consequences;
- remote task success cannot widen them.

### H: high assurance

- exact A2A release/source commit is reconstructable;
- Agent Memory-derived exports bind deterministically to action/input/scope;
- stale/revoked source evidence is explicit;
- raw content is represented by digest/ref by default;
- authority nonclaims remain machine-enforced by schema.

## V0.1 non-claims

V0.1 does not claim:

- A2A identity/authentication grants Agent Memory authority;
- Agent Cards are authorization documents;
- remote agents receive reusable Agent Memory grants;
- cross-agent context transfer is inheritance of authority;
- task acceptance/completion proves authorized local execution;
- peer Messages/Artifacts are trusted or true;
- peer output is automatically durable memory;
- A2A task state satisfies Agent Memory lifecycle obligations;
- A2A is required by Agent Memory implementations.

## Rollback / removal

The A2A adapter/profile is optional. Removing it leaves canonical Agent Memory state, decisions, corrections, revocations, and evidence interpretable because the normalized collaboration record references generic Agent Memory identities/receipts rather than embedding A2A runtime objects or making A2A identifiers canonical authority.

## Follow-on gate for authority-bearing transfer

Reusable or standing cross-agent authority is explicitly outside V0.1.

A future profile may consider authority-bearing transfer only after research #165/#172 produces an accepted implementation contract for:

```text
explicit authority-transition event
exact scope/action/material-condition binding
expiry
revocation
human ratification where required
recursive-learning prevention
proof that reusable authority was actually created
```

Historical approval or a successful A2A collaboration is insufficient.

## Stop line

Do not expand this profile into:

- an A2A client/server/SDK implementation;
- reusable cross-agent grants;
- automatic authority inheritance;
- cA2A as a mandatory dependency;
- upstream A2A protocol extensions;
- full memory-graph export;
- raw peer payload persistence;
- claims that A2A task completion proves Agent Memory lifecycle satisfaction.
