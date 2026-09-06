# DashClaw Live Cloudflare Conformance Plan

Status: **planned / not yet executed**

Tracking issue: [#361](https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/361)

Upstream interoperability issue: [`ucsandman/DashClaw#219`](https://github.com/ucsandman/DashClaw/issues/219)

Implementation predecessor: [#279](https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/279) / PR #305

## Purpose

Agent Memory already implements and tests the DashClaw external-verdict v1 provider contract and the governed durable-memory workload. The remaining proof is the real cross-system traversal through DashClaw's production guard/client over public HTTPS.

This plan keeps that proof intentionally small.

The Cloudflare endpoint is test transport for the canonical Agent Memory provider. It is **not** a production Agent Memory service and does not redefine PAMA, authority, mutation, recall, or receipt semantics.

## Ownership

This work is owned by Agent Memory.

QOR Agent previously supplied a successful Cloudflare proving environment for Agent Memory, native Microsoft Agent Governance Toolkit, AgentTrust, Qortara Governance, and Qortara SDLC. That environment is retained as deployment precedent and a reproducible proving asset, but it is not the DashClaw integration host.

```text
Agent Memory
  owns PAMA + provider semantics + governed mutation evidence

DashClaw
  owns guard invocation + applicability + stricter-wins composition + failure posture

Cloudflare Worker
  owns only public HTTPS transport for this conformance run

QOR Agent
  preserved prior proving asset; no DashClaw product responsibility
```

## Target topology

```text
DashClaw guard
    |
    | external-verdict v1 over public HTTPS
    v
agent-memory-dashclaw-provider-proving
    |
    +-- bearer verification
    +-- exact v1 request validation
    +-- exact input_identity echo
    +-- exact test authority resolution
    +-- canonical PAMA evaluation
    |
    v
allow | escalate | deny

later permitted/approved mutation
    |
    v
ordinary Agent Memory governed commit path
    |
    v
receipt / refusal / recall evidence
```

## Cloudflare account safety boundary

No live account mutation begins until an authorized Cloudflare-capable environment inventories the current account.

Every resource must be classified before deployment.

### Protected production

The DashClaw exercise must not alter resources serving unrelated production workloads, including Empty Flagon Inn and Celestara.

Protected means no:

- deletion;
- rename;
- route or DNS mutation;
- deployment replacement;
- secret mutation;
- binding mutation;
- storage mutation;
- account-wide cleanup operation.

### Preserved proving infrastructure

The completed QOR/AGT/AgentTrust proving stack is retained and is not modified for DashClaw. This includes its Workers, Workflows, Durable Object state, private R2 evidence, Service Bindings, secrets, deployment identities, and retained success/failure evidence.

### New disposable surface

The only new service owned by this plan is:

```text
agent-memory-dashclaw-provider-proving
```

No existing Cloudflare Worker is to be repurposed or exposed publicly merely to satisfy DashClaw.

## Provider dependency boundary

The provider decision surface should remain as small as practical.

Target separation:

```text
dashclaw_external_verdict
  wire validation
  identity/scope binding
  PAMA decision projection
  no memory mutation

dashclaw_governed_commit
  current-state revalidation
  approval binding
  governed commit / refusal
  receipt evidence
```

The provider must never gain mutation authority merely because it has been deployed to a public endpoint.

A refactor is permitted only where needed to keep the Worker dependency surface small. It must preserve the existing contract/adversarial tests and must not introduce a second PAMA implementation.

## Minimal Worker contract

Preferred source location:

```text
examples/cloudflare-dashclaw-provider/
```

Required public route:

```text
POST /v1/external-verdict
```

Required behavior:

1. require a bearer token;
2. accept only the expected JSON request shape;
3. pass the request to the canonical Agent Memory provider implementation;
4. use only exact test authority grants configured for the conformance workload;
5. echo DashClaw `input_identity` verbatim;
6. return bounded evidence;
7. expose no memory-mutation endpoint.

Expected Cloudflare resource surface:

```text
R2              = none
D1              = none
Durable Objects = none
Workflows       = none
Queues          = none
Cron            = none
Workers AI      = none
AgentTrust      = none
AGT             = none
QOR             = none
```

Expected secret surface:

```text
DASHCLAW_PROVIDER_TOKEN
```

No scheduled trigger and no polling are permitted.

## Cost and plan guard

No Cloudflare spend or plan upgrade is authorized by this test.

Before deployment, verify:

- the intended account is positively identified;
- the account remains on the intended free Workers plan;
- current Worker/resource names are inventoried;
- the new Worker name does not collide with an existing service;
- the bundle is comfortably within the free-plan size limit;
- no paid-plan-only binding or feature is present;
- no custom route or unrelated DNS mutation is required;
- dry/preflight packaging passes before remote mutation.

Stop instead of improvising if Cloudflare requests a paid plan, billing change, or unrelated account mutation.

## Canonical live workload

Use the stateful release-branch workload already defined and tested under #279.

### 1. Connection test

DashClaw sends:

```text
action_type = dashclaw.connection_test
```

Expected:

- public HTTPS reachability through the real DashClaw production client;
- exact `input_identity` echo;
- provider `allow` for a valid synthetic test;
- zero Agent Memory mutation state.

### 2. Initial promotion

```text
release_branch = release
operation = promotion
risk = low
```

Expected:

```text
PAMA allow_with_ledger
-> external allow
-> DashClaw effective decision
-> ordinary governed Agent Memory commit
```

### 3. Correction

```text
release_branch = main
operation = correction
risk = medium
```

Expected:

```text
PAMA require_review
-> external escalate
-> DashClaw require_approval
```

Then prove independently:

- missing approval refuses commit;
- wrong `input_identity` approval refuses commit;
- self-approval refuses commit;
- exact independent human approval satisfies only the review requirement for that mutation;
- Agent Memory revalidates current state and PAMA before commit;
- prior value is historical/superseded, not erased.

### 4. Stale replay

Replay the previously valid correction/approval after state advances.

Expected: refusal. Approval remains evidence rather than standing authority.

### 5. Scope / authority attack

Submit a materially broader or foreign-project mutation.

Expected:

```text
external deny
-> DashClaw stricter block/equivalent
-> zero Agent Memory substrate mutation
```

### 6. Provider unavailable

Make the provider unavailable for an in-scope mutation.

Expected:

- DashClaw records external-provider unavailability as an availability fact;
- the configured fail-closed posture applies;
- no Agent Memory allow/deny verdict is fabricated.

## Evidence contract

The passing report preserves two evidence chains.

### DashClaw

```text
request_id
input_identity
local decision
external decision
external provider status
effective decision
provider reason
provider policy version
approval identity/reference where applicable
failure posture
```

### Agent Memory

```text
proposal_id
proposal_digest
content digest
authority evidence
PAMA policy version/outcome
state snapshot
approval binding where applicable
commit/refusal
receipt
after-state current-memory reference
later governed recall/admission evidence
```

Correlation is required. Identity collapse is forbidden.

```text
DashClaw decision != Agent Memory execution
DashClaw approval != standing Agent Memory authority
DashClaw input_identity != Agent Memory proposal digest
provider decision evidence != commit receipt
```

## Pass criteria

The live integration passes only when all of the following are demonstrated:

- real DashClaw `allow`, `escalate`, and `deny` traverse the external-provider seam;
- the real DashClaw connection test succeeds;
- input identity is preserved exactly;
- a permitted mutation commits through the ordinary Agent Memory path;
- correction requires independent human approval and supersedes history;
- stale replay is refused;
- scope/authority expansion is denied;
- provider unavailability is explicit and fail-closed according to DashClaw posture;
- DashClaw and Agent Memory evidence remain reconstructably distinct;
- discovered defects are recorded with remediation/retest evidence.

The resulting report must be linked from both Agent Memory #361 and DashClaw #219.

## Stop conditions

Stop and record the blocker if:

- a paid Cloudflare plan or billing change is requested;
- current account inventory cannot safely distinguish protected resources from this test surface;
- deployment tooling proposes mutation of an existing Worker/route/storage resource not owned by this plan;
- satisfying #219 appears to require AgentTrust, AGT, QOR, Qortara Governance, or Qortara SDLC;
- live execution exceeds the bounded test window because a real integration defect has been discovered;
- evidence cannot distinguish provider decision from memory execution.

## Closeout posture

After DashClaw #219 acceptance:

- update the Agent Memory runtime-evidence record with the live results;
- post the correlated evidence/result to DashClaw #219;
- retain the tiny Worker idle only if it has a near-term use for DashClaw #220 or another conformance run;
- otherwise disable/remove only this test endpoint according to its runbook;
- preserve source, deployment identity, and evidence;
- leave the QOR proving environment parked and preserved;
- do not touch Empty Flagon Inn or Celestara.

## Non-goals

- no QOR Agent product expansion;
- no public exposure of the parked QOR proving orchestrator;
- no AGT/ACS conformance in this plan;
- no AgentTrust re-test;
- no Qortara Governance or Qortara SDLC dependency;
- no Cloudflare spend;
- no production Agent Memory service claim;
- no modification of unrelated Cloudflare production workloads;
- no claim of process-restart safety beyond the boundaries already tracked by Agent Memory restart-safety work.
