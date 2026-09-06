# External Enforcement Decision Projection Profile

## Purpose

This profile defines the smallest vendor-neutral boundary needed to carry an Agent Memory governed mutation decision to an optional external policy or enforcement host without surrendering memory-specific semantics.

It implements the Phase 1 contract work of issue #152 and is now behaviorally proven against two materially different real deterministic policy hosts: Open Policy Agent (OPA) and Cedar. Both remain optional reference peers, not required Agent Memory dependencies.

The responsibility split is:

```text
Agent Memory
  owns memory semantics, lifecycle, scope, correction,
  PAMA authority, recall admission, and mutation meaning
        |
        v
External Enforcement Decision Projection
  content-minimized action + authority context
        |
        v
optional external policy decision
        |
        v
explicit monotonic composition
        |
        v
enforcement / approval host
```

The same product may implement more than one box. The evidence contracts remain distinct.

## Core invariants

### Stricter authority is monotonic

A decision from one authority may tighten another authority's result. It may not silently loosen it.

```text
Agent Memory deny + external allow          -> deny
Agent Memory require_approval + external allow -> require_approval
Agent Memory allow + external deny          -> deny
Agent Memory allow + external escalate      -> require_approval
```

### Decision is not enforcement

```text
decision issued
!=
decision delivered
!=
enforcement point reached
!=
action executed or prevented
```

A projection or composition receipt proves only the decision information it records. It does not prove that a downstream host enforced that result.

### Proposal identity stays bound

An external decision is usable only when it binds to the exact `input_identity` calculated for the projected proposal. A stale, mismatched, or detached decision fails closed under the configured provider posture.

### Memory semantics remain local

An external provider may contribute broader runtime policy. It does not redefine:

- correction versus supersession;
- rejection and governed re-admission;
- lifecycle state;
- memory isolation domains;
- PAMA target class;
- recall admission;
- deletion completeness;
- whether a memory-specific mutation actually occurred.

## Projection shape

The first profile carries only information needed to identify and constrain the requested consequence.

```text
projection_id
projection_version
input_identity
proposal_id
memory_id / target_reference
operation
actor_id
scope
isolation_domain_refs
state_snapshot
risk_class
reversibility
pama_decision_ref
pama_outcome
permitted_actions
prohibited_actions
policy_version
evidence_refs
receipt_ref, when available
```

The projection does not require raw memory content, prompts, rationale prose, or retrieved context.

`input_identity` is a deterministic SHA-256 identity over the canonical projection inputs that define the requested action and its authority state. The reference implementation uses deterministic canonicalization before cross-provider composition.

## Normalized composition lattice

External systems use different vocabularies. V0.1 normalizes only the smallest common consequence lattice:

```text
allow < warn < require_approval < deny
```

Agent Memory PAMA maps conservatively:

```text
allow                         -> allow
allow_with_ledger             -> allow
require_review                -> require_approval
require_external_verification -> require_approval
abstain                       -> require_approval
collect_more_evidence         -> require_approval
quarantine                    -> deny
block                         -> deny
```

An optional external provider V0.1 may return:

```text
allow
warn
escalate
deny
```

with the adapter mapping:

```text
allow    -> allow
warn     -> warn
escalate -> require_approval
deny     -> deny
```

V0.1 deliberately excludes provider-directed mutation transforms. A provider may not silently rewrite the memory proposal and then claim it evaluated the original action. Transform-like systems require a later explicit identity-preserving contract.

The effective decision is the stricter normalized consequence.

## External decision record

A provider response should preserve at least:

```text
provider_id
provider_version
input_identity
decision
reason
evidence
issued_at
```

`reason` and provider evidence are provenance for the external decision. They do not become Agent Memory truth merely because the provider is trusted to make policy decisions.

Provider-specific revision, package, rule, bundle, source identity, policy artifact digest, determining policy ID, or equivalent reconstructability metadata may travel inside the bounded `evidence` object. Such metadata does not become a new canonical Agent Memory authority field merely because one provider exposes it.

## Provider posture

Provider availability must be explicit.

### Advisory provider

The provider may tighten a local decision when it responds. If unavailable, the local Agent Memory decision remains authoritative and the result records that external policy was unavailable.

```text
provider_mode = advisory
provider unavailable
-> effective decision = local PAMA mapping
-> external governance status = unavailable
```

This is not a claim that external policy approved the action.

### Authoritative provider

The configured external provider is required for the action class.

```text
provider_mode = authoritative
provider unavailable / invalid / stale
-> deny
```

This is the reference fail-closed posture. Implementations may define a different stricter posture, but may not treat provider failure as implicit allow.

## Approval continuity

When `require_approval` is the effective result:

- approval must bind to the same `input_identity`;
- state drift requires a new projection and decision;
- approval cannot broaden scope or change the memory operation silently;
- the approval principal and authority evidence remain separate from the memory proposal itself;
- approval satisfaction still does not prove execution.

An external provider returning `allow` is not an approval record and cannot discharge an Agent Memory `require_approval` consequence.

The existing durable-decision overwrite and shared-write coordination evidence demonstrate the same general rule inside Agent Memory: a valid coordination or approval artifact is not a bypass token for PAMA.

## Decision composition receipt

The composition layer should be able to record:

```text
composition_id
input_identity
local_decision_ref
local_normalized_decision
external_decision_ref, when present
external_provider_status
external_normalized_decision, when present
effective_decision
composition_rule_version
execution_evidence_ref, when available
execution_status
```

For Phase 1, `execution_status` is limited to explicit non-claims such as:

```text
unknown
not_observed
```

A future enforcement-evidence slice may define stronger states only when an actual enforcement witness can substantiate them.

## Required Phase 1 adversarial cases

### External allow cannot loosen local block

```text
local = deny
external = allow
expected = deny
```

### External allow cannot discharge local review

```text
local = require_approval
external = allow
expected = require_approval
```

### External deny tightens local allow

```text
local = allow
external = deny
expected = deny
```

### External escalation tightens local allow

```text
local = allow
external = require_approval
expected = require_approval
```

### Stale action identity

```text
external.input_identity != current projection.input_identity
expected = invalid external decision
```

Under authoritative provider mode the effective result is deny. Under advisory mode the invalid result is ignored as policy authority and the local decision remains, with mismatch evidence preserved.

### Provider unavailable

```text
advisory provider unavailable      -> local decision + unavailable evidence
authoritative provider unavailable -> deny
```

### Decision issued, execution unknown

```text
valid composed decision exists
execution witness absent
expected execution_status = unknown
```

No conformance report may upgrade that state to enforced, prevented, or executed by inference.

## First real policy-host proof: Open Policy Agent

The generic seam is behaviorally proven against OPA `v1.19.0`, exact source commit `1e32c796e8979b1bda2f768138500b1deb95ff24`.

The dedicated comparator verifies the official Linux amd64 release artifact against SHA-256:

```text
4ae5eeec241c9f5df7c5f566fe96e26336ce186f8c773c46ffdf10b48189a520
```

It then validates a Rego v1 comparator policy and evaluates real projections with the real OPA CLI.

### Minimized OPA input

OPA receives an explicit subset of the already-minimized projection:

```text
input_identity
proposal_id
memory_id
operation
actor_id
scope
tenant_ref
purpose
state_snapshot
risk_class
reversibility
pama_decision_ref
pama_outcome
permitted_actions
prohibited_actions
policy_version
```

It does not require raw memory content, evidence payloads, prompts, hidden reasoning, or retrieved context.

### Real monotonic matrix

The pinned real OPA engine proves:

```text
native allow + OPA allow              -> allow
native allow + OPA deny               -> deny
native require_approval + OPA allow   -> require_approval
native deny + OPA allow               -> deny
```

This confirms the first external policy host can tighten Agent Memory consequence but cannot loosen PAMA.

### OPA policy revision

The comparator policy returns an explicit policy revision. The OPA adapter compares it with the expected pinned revision **before** building a valid generic external decision.

```text
expected revision == observed revision
-> normalize external decision
-> generic composition

expected revision != observed revision
-> adapter marks stale policy revision
-> no valid external decision reaches generic composition
-> configured advisory/authoritative provider-failure posture applies
```

OPA revision is therefore adapter evidence, not a new canonical composition field.

The real-host proof did not require a generic schema change for OPA revision semantics.

### Stale Agent Memory input identity

The comparator also reuses one valid real OPA decision against a different current Agent Memory projection.

The existing generic composition layer detects the mismatched `input_identity` and records stale identity. No OPA-specific identity exception is needed.

### Decision remains distinct from enforcement

A successful real OPA evaluation still produces a composition receipt with:

```text
execution_status = unknown
```

OPA's policy decision does not prove:

- the action executed;
- an enforcement point was reached;
- the action was prevented;
- a human approved the action;
- durable Agent Memory state changed.

The comparator creates no canonical memory write merely because OPA returned a decision.

### Generic finding from the first host

OPA required no provider-specific canonical composition semantics.

Its package, rule, policy revision, release, and source pin fit inside external decision evidence. Its `allow`/`deny` result fits the existing normalized consequence lattice. Its input binding uses the existing Agent Memory `input_identity`.

```text
real OPA decision mechanics
-> existing external decision builder
-> existing monotonic composition receipt
```

That is the result the first real peer was intended to test.

## Second real policy-host proof: Cedar

The same generic seam is now behaviorally proven against Cedar `v4.12.0`, exact tag commit `fdcbaed32bdb8c8d13e4eaf2b58db5555e9fb8c5`.

The dedicated workflow builds `cedar-policy-cli` from that exact Git source under the release's Rust 1.89 minimum toolchain, verifies the installed Cedar 4.12.0 binary, verifies the checked-in policy artifact SHA-256, and executes the comparator against the real engine.

### Why Cedar is a meaningful second host

Cedar's result shape is materially different from the OPA comparator.

OPA can return an arbitrary structured value that echoes Agent Memory metadata. Cedar `authorize` instead evaluates an explicit principal/action/resource/context request and returns `ALLOW` or `DENY` plus diagnostics such as determining policy IDs.

The Cedar adapter therefore owns request/result binding:

```text
Agent Memory input_identity
+ principal / action / resource / minimized context
+ exact policy artifact SHA-256
-> real Cedar authorize
-> ALLOW / DENY + determining policy IDs
-> adapter binds result to the exact request it executed
-> existing generic external decision
-> existing generic composition
```

No Cedar-specific field was added to the canonical composition schemas.

### Minimized Cedar request

The reference comparator maps only the bounded request identity and action context:

```text
principal <- actor_id
action    <- operation
resource  <- memory_id
context   <- input_identity
             purpose
             risk_class
             scope
             tenant_ref
             pama_outcome
             policy_version
```

Raw memory content, prompts, hidden reasoning, arbitrary evidence payloads, and retrieved context are not required.

### Real Cedar monotonic matrix

The pinned real Cedar engine proves:

```text
native allow + Cedar allow              -> allow
native allow + Cedar deny               -> deny
native require_approval + Cedar allow   -> require_approval
native deny + Cedar allow               -> deny
```

Cedar can therefore tighten a native Agent Memory consequence without gaining a path to loosen PAMA.

### Policy artifact identity versus provider revision

Cedar CLI does not return an arbitrary policy-revision field. The adapter instead binds decision evidence to the exact policy artifact under evaluation:

```text
policy_ref
policy_sha256
cedar_release
cedar_source_commit
determining_policy_ids
request_digest
```

A mismatched expected policy digest is rejected at the adapter edge before any valid external decision reaches generic composition. Advisory versus authoritative failure posture is then handled by the existing generic rules.

This demonstrates a useful cross-provider result: reconstructable provider policy identity belongs in bounded external evidence, while the generic composition contract needs only stable decision and Agent Memory input identity semantics.

### Cedar DENY is not provider failure

The pinned Cedar CLI uses exit code `2` for a completed authorization request whose decision is `DENY`. The adapter therefore treats that documented return code as a valid policy result and distinguishes it from actual CLI/provider failure.

The distinction matters:

```text
policy evaluated and denied
!=
policy engine failed to evaluate
```

### Stale Agent Memory input identity remains generic

A valid Cedar decision is rebound to the Agent Memory `input_identity` of the exact request the adapter executed. Replaying that normalized decision against another projection is rejected by the same generic stale-identity gate used for OPA.

No Cedar-specific replay exception is needed.

### Decision remains distinct from enforcement

Successful Cedar authorization still produces:

```text
execution_status = unknown
```

Cedar ALLOW or DENY is policy-decision evidence. It is not approval, an enforcement witness, execution evidence, lifecycle satisfaction, or canonical Agent Memory state.

## Generic finding after two materially different hosts

OPA and Cedar differ significantly in policy language, request/result shape, and how reconstructable policy identity is surfaced. Both nevertheless fit the same core contract:

```text
Agent Memory semantics / PAMA
-> minimized current-action projection
-> provider-specific adapter
-> external policy decision bound to exact input_identity
-> monotonic composition
-> separate approval / enforcement / execution evidence
```

The two-host proof therefore strengthens the claim that the generic seam is provider-neutral at this boundary. It does **not** imply that every authorization system will fit without further research, or that a third engine should be added merely to accumulate logos.

## Relationship to existing Agent Memory contracts

This profile composes with existing artifacts rather than replacing them:

- PAMA decision remains authoritative for Agent Memory mutation semantics;
- decision receipt records the selected Agent Memory consequence;
- portable governance evidence may correlate a completed Agent Memory decision with external trust systems;
- Governance Context Projection carries remembered context/precedent outward and does not become this action-decision projection;
- execution evidence remains a separate surface;
- real OPA and Cedar policy evaluations remain external decision evidence and do not become memory state merely because they are deterministic.

The outbound directions are therefore distinct:

```text
Governance Context Projection
  remembered context / precedent
  -> external decision input

External Enforcement Decision Projection
  current requested memory consequence + PAMA boundary
  -> policy / enforcement host

Portable governance evidence
  recorded decision / action evidence
  -> verifier / attestation consumer
```

## Follow-on gate

The #166 two-host policy-abstraction gate is now satisfied by OPA and Cedar.

A third policy peer should be added only when it tests a **materially different responsibility or failure mode**, not merely another allow/deny API. Examples may include relationship-based authorization state, embedded authorization libraries, identity-rich local PDP deployment, or a standards-shaped access-evaluation surface.

Cedarling research is tracked separately because its potential value is primarily deployment, identity/token handling, policy-store evidence, local PDP operation, OPA bridging, and AuthZen exposure rather than proving Cedar's policy semantics a second time.

## Non-goals

- making Agent Memory a universal PDP;
- adopting Microsoft AGT, DashClaw, OPA, Cedar, Cedarling, or another provider as a required dependency;
- importing a vendor policy language into memory doctrine;
- allowing external `allow` to weaken PAMA;
- treating a decision receipt as execution proof;
- exporting raw memory content when stable references and characteristics suffice;
- supporting transform-style provider verdicts in V0.1;
- using provider policy revision, policy digest, or determining policy ID as standing Agent Memory authority;
- treating OPA or Cedar policy evaluation as approval or enforcement evidence.

## Doctrine boundary

The reusable rule is:

> **External governance may narrow Agent Memory's permitted consequence, but it cannot silently widen it, and neither decision layer may claim enforcement without execution evidence.**