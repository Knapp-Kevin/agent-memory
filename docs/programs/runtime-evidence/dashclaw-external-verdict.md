# DashClaw External-Verdict Provider Evidence

Status: **implementation evidence / #279 provider-side slice**

This document records the executable Agent Memory side of DashClaw's external-verdict v1 interoperability contract. It does not claim the final live cross-repository integration is complete.

## Evidence boundary

DashClaw contract:

```text
release: v5.24.0
commit:  082b704262bebe0e86ef66d98c97f42d6358c3c3
wire:    external-verdict v1
```

The focused workflow fetches that exact source revision, verifies that the annotated `v5.24.0` tag dereferences to the same commit, and preserves the upstream implementer guide with the Agent Memory workload evidence.

DashClaw v5.24.0 also resolves the domain-applicability question raised during #279. A configured provider can be scoped by exact `action_type` through DashClaw's host-side `EXTERNAL_VERDICT_ACTION_TYPES` setting. For this integration the intended scope is:

```text
agent_memory.mutation
```

Out-of-scope actions are not sent to Agent Memory. DashClaw records them as `not_applicable` locally rather than manufacturing an external `allow`. Its built-in `dashclaw.connection_test` intentionally bypasses that scope so the wire itself remains testable.

## Runtime shape

```text
DashClaw Decide
  |
  | external-verdict v1 request
  v
Agent Memory DashClaw adapter
  |
  +-- validate wire + exact memory-content binding
  +-- bind DashClaw org/agent identity
  +-- resolve requested project scope through trusted authority evidence
  +-- evaluate existing PAMA policy
  |
  v
allow | escalate | deny
  |
  +-- decision projection only

later permitted/approved mutation
  |
  +-- re-resolve authority over requested scope
  +-- re-resolve current actor authority over existing target scope
  +-- exact approval/input binding where review is required
  +-- independent PAMA re-evaluation
  +-- current-state / stale-state check
  v
DashClawGovernedCommitter
  |
  v
GovernedMemoryAdapter.commit_proposal
  |
  v
mutation + canonical receipt or refusal
```

The load-bearing separations are:

```text
identity != scope authority
requested-scope authority != authority over an existing target scope
DashClaw verdict != Agent Memory execution
DashClaw approval != standing Agent Memory authority
DashClaw input_identity != Agent Memory proposal digest
provider decision evidence != commit receipt
```

## Provider request and identity rules

The adapter accepts DashClaw's frozen v1 request fields:

```text
request_id
org_id
agent_id
action_type
declared_goal
act
input_identity
```

`input_identity` is owned by DashClaw and echoed byte-for-byte. Agent Memory does not attempt to reproduce DashClaw's canonicalization algorithm.

The mutation payload uses:

```text
act.kind = agent_memory.mutation
act.memory_value = exact retained value
act.proposal = bounded PAMA proposal inputs
```

The exact memory value is bound by:

```text
proposal.content_sha256 = sha256(memory_value)
```

A content mismatch is denied before PAMA evaluation, so a verdict for one value cannot be reused for another.

## Identity is not scope authority

DashClaw's top-level fields provide trusted peer identity bindings:

```text
org_id   -> Agent Memory tenant/org identity
agent_id -> proposing actor identity
```

They do **not** prove that the actor may mutate any project/task scope named inside `act`.

The adapter therefore accepts a separate `AuthorityResolver` that reconstructs the requested isolation-domain authority. Without a resolver, the proposal reaches PAMA with:

```text
actor_authority_resolved = false
```

and PAMA blocks it. An authorized resolution must also return a reconstructable `evidence_ref`; an unexplained boolean allow is rejected.

The reference integration includes a deliberately narrow `StaticAuthorityResolver` for already-configured grants and wraps it in `ProjectScopedAuthorityResolver` for this #279 profile. The project wrapper enforces:

```text
project_ref is required
proposal.scope == project_ref
project_ref is a bound isolation domain
task_ref, when present, is a bound isolation domain
```

This prevents authenticated organization identity from turning into organization-wide memory mutation authority. A grant for `project:fixture` does not authorize an org-only mutation request merely because the request has the correct `org_id`.

The nested `act.proposal` is not allowed to inject replacements for:

```text
actor_id
tenant_ref
actor_authority_resolved
approval_refs
review_satisfied
```

The adapter also binds the DashClaw org as `org:<org_id>` in proposal isolation evidence and refuses a conflicting `org:` domain supplied by the act.

## Requested scope is not current target scope

A second authority check is required when a logical memory target already exists.

A stateless provider verdict can prove that an actor is authorized to request a mutation in Project A. It cannot, by that fact alone, prove that an existing logical `target_reference` belongs to Project A. If the current memory with that logical ID is actually bound to Project B, a Project A correction must not supersede it.

`DashClawGovernedCommitter` therefore records process-local target-scope facts after successful commits:

```text
memory_id
org_id
scope
project_ref
task_ref
isolation_domain_refs
authority_evidence_ref
```

The binding deliberately does **not** store the creating actor as future authority. On every later mutation, it constructs a new authority request using the **current acting identity** and the target's existing stored scope.

For a normal correction/promotion:

```text
current actor authorized for requested scope
AND
current actor authorized for existing target scope
AND
requested scope == existing target scope
```

must hold before the ordinary governed commit seam is reached.

If a target already exists in `GovernedMemoryAdapter` but its scope binding is missing from the #279 committer registry, the integration fails closed with:

```text
target_scope_unresolved
```

That is intentional. The target-scope registry is governance-critical state. It is process-local in this slice and is another concrete item #282 must persist or reconstruct before restart safety can be claimed.

## PAMA projection

The adapter uses the existing deterministic PAMA evaluator. It does not introduce a second policy language.

```text
PAMA allow                          -> DashClaw allow
PAMA allow_with_ledger              -> DashClaw allow
PAMA require_review                 -> DashClaw escalate
PAMA require_external_verification  -> DashClaw escalate
PAMA block                          -> DashClaw deny
```

No synthetic `warn` state is invented.

Provider evidence records the authority-resolution posture, PAMA outcome/version, proposal/content bindings, and explicitly records:

```text
execution_evidence = false
```

It is bounded under DashClaw's 4096-character provider-evidence ceiling.

## Connection test

`dashclaw.connection_test` is handled explicitly and side-effect free.

A valid synthetic test receives a contract-valid `allow` response with the DashClaw identity echoed. No authority grant is required because no memory mutation follows. No proposal is committed and no Agent Memory memory/receipt state is created.

A malformed top-level request that lacks the identity required for a valid echo receives a non-2xx HTTP response from the reference server. Fabricating a contract verdict without the required identity would be less honest than allowing DashClaw to apply its configured provider-unavailability posture.

## Approval and commit boundary

A DashClaw `escalate` is only a provider decision. It does not commit a mutation.

When PAMA requires review, the later Agent Memory commit seam requires separate approval evidence:

```text
approval_ref
approval_actor_id
approved_input_identity
```

The commit seam refuses when:

- approval evidence is missing;
- the approved DashClaw `input_identity` does not equal the exact mutation identity;
- the approving actor is the same agent that proposed the mutation.

After scope/target-scope checks and approval binding, the proposal is passed through `GovernedMemoryAdapter.commit_proposal`, which independently re-evaluates PAMA and current state. A valid approval therefore cannot make a stale proposal current again.

## Executed workload

The deterministic workload is the #279 release-branch scenario plus authority attacks.

### Authority precondition

The same well-formed promotion request is first evaluated without an authority resolver. DashClaw identity is present, but project mutation authority is unresolved, so PAMA blocks the request.

The fixture then supplies separately configured exact grants for two actors in two different projects. Only a matching project grant proceeds to the normal PAMA outcome.

### Initial promotion

```text
release_branch = release
operation = promotion
risk = low
state = v0
```

Executed behavior:

```text
scope authority resolved
-> PAMA allow_with_ledger
-> provider allow
-> target-scope commit guard
-> ordinary governed commit
-> receipt emitted
-> later governed recall admits current project memory
```

### Correction

```text
release_branch = main
operation = correction
risk = medium
state = v1
```

Executed behavior:

```text
scope authority resolved
-> PAMA require_review
-> provider escalate
-> unapproved commit refused
-> wrong input_identity approval refused
-> self-approval refused
-> exact external approval accepted as evidence
-> current target scope revalidated for acting identity
-> Agent Memory independently revalidates
-> correction commits
-> old release value becomes superseded/event-invalid
-> main becomes current and recall-admissible
```

### Stale replay

Replaying the previously approved correction after state advances to `v2` produces:

```text
committed = false
refusal = stale_authorization
```

The approval remains authentic evidence but does not become standing authority over changed state.

### High-authority scope attack

A critical `scope_expansion` targeting M5/A5 inside the actor's resolved project context resolves to PAMA `block`, projects to DashClaw `deny`, and is refused before the substrate write log changes.

### Unauthorized requested project

A low-risk request from `release-agent` naming `project:other` is denied because no matching authority grant exists. The substrate remains untouched.

### Cross-target logical identity attack

The harness seeds a second logical release-branch memory under `project:other` using an independently authorized `other-project-agent`.

Then `release-agent`, which is legitimately authorized for `project:fixture`, submits a correction against the **Project B logical target ID** while requesting Project A scope.

The stateless provider projection sees a valid Project A request and returns `escalate`, which is correct for the information available to that layer. The stateful committer then reconstructs the target's current Project B scope and asks whether `release-agent` controls it. It does not, so the commit is refused with:

```text
target_scope_authority_unresolved
```

The Project B fact remains unchanged and the substrate write log does not advance.

This demonstrates why:

```text
valid provider verdict
!= sufficient execution authority
```

### Cross-project recall

The same-tenant substrate can return matching candidates from several projects. Governed admission admits only the matching project context and rejects foreign-project candidates. Candidate presence remains distinct from recall permission.

## Reference surfaces

Pure wire/PAMA adapter:

`reference/agentmem_ref/dashclaw_external_verdict.py`

Stateful target-scope commit guard:

`reference/agentmem_ref/dashclaw_governed_commit.py`

Reference HTTP entrypoint:

`reference/run_dashclaw_provider.py`

Deterministic workload:

`reference/run_dashclaw_external_verdict.py`

Adversarial tests:

- `reference/tests/test_dashclaw_external_verdict.py`
- `reference/tests/test_dashclaw_project_authority.py`

Focused evidence workflow:

`.github/workflows/dashclaw-external-verdict.yml`

The HTTP entrypoint is intentionally a small standard-library server. DashClaw requires a public HTTPS provider URL, so a live integration must place this reference endpoint behind controlled public HTTPS or deploy an equivalent production-grade service. The reference server itself is not claimed as a production deployment architecture.

For controlled integration, the reference server accepts `--authority-grants-file` containing explicit org/agent/project/isolation-domain grants. It wraps those grants in the project-scoped authority profile. If omitted, mutation authority remains unresolved and mutation requests deny. A real deployment should replace the static resolver with an appropriate trusted identity/authorization source rather than treating the grant file as product architecture.

## Current limitations / remaining #279 work

This slice proves the provider contract and the stateful Agent Memory workload in the Agent Memory repository. It does **not** yet prove that the request traversed a live DashClaw guard over public HTTPS.

Still required before #279 closes:

- configure a live DashClaw v5.24+ org with provider scope `agent_memory.mutation`;
- run `dashclaw.connection_test` through DashClaw's production wire client;
- execute real `allow`, `escalate`, and `deny` through DashClaw's guard seam;
- connect the deployed adapter to a trusted project-authority resolver rather than assuming identity implies scope authority;
- capture DashClaw local/external/effective decision evidence and correlate it to the later Agent Memory proposal/receipt without collapsing their identities;
- exercise provider unavailable behavior through DashClaw and verify the configured posture is represented honestly;
- record the cross-repository integration result and any contract defects found.

This slice proves only cross-session reuse within one governed runtime. It does not prove process-restart durability. In particular, the new target-scope binding registry is process-local:

```text
persistent memory substrate
!= persisted target-scope authority binding
!= restart-safe governed memory
```

Restart-safe governance metadata remains #282.
