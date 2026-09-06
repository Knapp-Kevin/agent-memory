# DashClaw Cloudflare Provider Proving Example

Status: **test-only / live conformance transport**

Tracking: [Agent Memory #361](https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/361) · [DashClaw #219](https://github.com/ucsandman/DashClaw/issues/219)

This example exposes the already-tested Agent Memory/PAMA DashClaw external-verdict provider through one minimal public Cloudflare Python Worker.

It is deliberately **not** a production Agent Memory service. It exposes no mutation endpoint, persists no state, and has no R2, D1, Durable Object, Workflow, Queue, Cron, Workers AI, AGT, AgentTrust, QOR, Qortara Governance, or Qortara SDLC dependency.

## Authority boundary

```text
DashClaw v5.32.0 guard
    |
    | external-verdict v1 / public HTTPS
    v
agent-memory-dashclaw-provider-proving
    |
    +-- bearer verification
    +-- DashClaw v1 request validation
    +-- exact input_identity echo
    +-- project-scoped trusted test authority
    +-- canonical Agent Memory/PAMA evaluation
    |
    v
allow | escalate | deny
```

The Worker is decision projection only:

```text
provider decision != Agent Memory execution
DashClaw approval != standing Agent Memory authority
```

Any actual permitted/approved mutation still goes through the ordinary Agent Memory governed commit path and independently revalidates authority, PAMA, current state, and approval binding.

## Why Python Worker

Agent Memory's reference PAMA/provider implementation is Python and stdlib-only at the decision boundary. Cloudflare Python Workers execute CPython semantics through Pyodide, so this proving transport can run the canonical provider logic rather than creating a second JavaScript PAMA implementation.

`prepare.py` copies the exact canonical sources from `reference/agentmem_ref/` into the generated Worker source tree and records SHA-256 identities. The only packaging transformation makes the stateful `GovernedMemoryAdapter` import type-checking-only. Provider behavior is otherwise unchanged.

The generated `src/agentmem_ref/` directory is ignored by Git and must not become another manually maintained implementation.

## Hard account safety boundary

Before **any remote Cloudflare mutation**, inventory the intended account from an authorized Cloudflare-capable environment.

Classify and protect at least:

```text
PROTECTED PRODUCTION
  Empty Flagon Inn
  Celestara
  all related Workers, routes, domains, secrets and storage

PRESERVED PROVING INFRASTRUCTURE
  QOR / AGT / AgentTrust proving Workers
  Qortara Governance / SDLC proving services
  proving R2 buckets, Workflows, Durable Objects, Service Bindings and evidence

THIS ISSUE OWNS ONLY
  agent-memory-dashclaw-provider-proving
```

Do not delete, rename, replace, rebind, reroute, rotate secrets for, or otherwise mutate unrelated resources while performing this run.

No plan upgrade or Cloudflare spend is authorized by #361. Stop if deployment tooling requests either.

## Local preparation

From this directory:

```bash
python prepare.py --check
python prepare.py
```

`--check` performs the packaging/importability check in a temporary directory and leaves the working tree unchanged. The normal command writes the generated provider package under `src/agentmem_ref/` and prints the canonical/prepared source hashes.

## Provider configuration secret

The Worker has one encrypted Cloudflare secret:

```text
DASHCLAW_PROVIDER_CONFIG
```

Its JSON value contains both the bearer credential and the exact reference-only authority grants for the test workload:

```json
{
  "bearer_token": "<high-entropy-test-token>",
  "authority": {
    "grants": [
      {
        "org_id": "<dashclaw-test-org-id>",
        "agent_id": "<dashclaw-test-agent-id>",
        "isolation_domain_refs": ["project:fixture"],
        "evidence_ref": "operator-configured:dashclaw-live-conformance"
      }
    ]
  }
}
```

Do not commit the populated value. Keep it in a local ignored file or pipe it directly to Wrangler when provisioning the secret.

The project-scoped resolver requires an exact `project_ref`; authenticated DashClaw org/agent identity alone does not become organization-wide memory mutation authority.

## Dry-run before account mutation

Cloudflare Python Workers are deployed with `pywrangler`. Use an isolated invocation rather than the repository root dependency set:

```bash
uvx --from workers-py pywrangler deploy --dry-run --outdir dist
```

Before proceeding, inspect the output and confirm all of the following:

- Worker name is exactly `agent-memory-dashclaw-provider-proving`;
- the endpoint uses `workers.dev`; no custom route or DNS change is proposed;
- no R2/D1/DO/Workflow/Queue/Cron/Workers-AI/service binding appears;
- the bundle is comfortably within the current free-plan size limit;
- only the intended Worker is being prepared;
- no plan/billing change is requested.

If any condition is false, stop and update #361 rather than improvising around it.

## Remote deployment sequence

Only after the account inventory and dry run are clean:

1. Confirm the account remains on the intended Cloudflare Workers Free plan.
2. Confirm the Worker name does not collide with an existing service.
3. Provision `DASHCLAW_PROVIDER_CONFIG` on this Worker only.
4. Deploy `agent-memory-dashclaw-provider-proving`.
5. Record the deployment identity and source revision in #361.
6. Verify no unrelated Cloudflare resource changed.

Do not add a scheduled trigger. This endpoint should receive requests only when the integration test deliberately calls it.

## DashClaw configuration

Use current DashClaw **v5.32.0** for the live run. The maintainer confirmed that the external-verdict wire contract, applicability filter, and posture handling remain unchanged from the previously tested line.

In `/policies`, configure the provider with:

```text
URL:          https://<worker>.workers.dev/v1/external-verdict
Bearer token: value matching bearer_token in DASHCLAW_PROVIDER_CONFIG
Action types: agent_memory.mutation
Posture:      fail_closed
Timeout:      within DashClaw's supported 100-5000 ms range
```

`fail_closed` is intentional for the outage test. Under DashClaw's contract, an unavailable provider then becomes `require_approval`, while the evidence remains explicitly `external unavailable` rather than fabricating an Agent Memory verdict.

## Live acceptance sequence

### 1. Connection test

Use DashClaw's **Test provider** control.

Expected:

```text
action_type = dashclaw.connection_test
provider allow
exact input_identity echo
zero Agent Memory mutation state
```

### 2. Initial governed promotion

```text
release_branch = release
operation = promotion
risk = low
```

Expected:

```text
PAMA allow_with_ledger
-> external allow
-> DashClaw stricter-wins effective decision
-> ordinary Agent Memory governed commit
```

### 3. Correction and approval

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

Then prove that missing approval, wrong `input_identity`, and self-approval all refuse commit; only exact independent human approval may satisfy the review evidence, after which Agent Memory revalidates PAMA and current state before committing.

### 4. Stale replay

Replay the previously valid correction/approval after state advances.

Expected: Agent Memory refuses the stale mutation. Approval remains evidence, not standing authority.

### 5. Scope/authority attack

Submit the canonical high-authority or foreign-project attack.

Expected:

```text
external deny
-> DashClaw block
-> no Agent Memory substrate mutation
```

DashClaw confirms external `deny` maps to `block` regardless of local grant or calibration state.

### 6. Provider unavailable

Make only this test provider unavailable for an in-scope mutation while DashClaw is configured `fail_closed`.

Expected:

```text
external unavailable
-> fail_closed posture
-> require_approval
```

The evidence must say unavailable. It must not say Agent Memory allowed or denied the act.

## Evidence to retain

DashClaw decision chain:

```text
request_id
input_identity
local decision
external decision
external status
effective decision
provider reason
provider policy version
approval reference
posture
```

Agent Memory chain:

```text
proposal_id
proposal_digest
content digest
authority evidence
PAMA version/outcome
state snapshot
approval binding
commit/refusal
receipt
current-memory reference
later governed recall/admission evidence
```

Correlate the chains without collapsing their identities.

## Closeout

After DashClaw #219 accepts the run:

- post the correlated result to DashClaw #219 and Agent Memory #361;
- record any defect, remediation, and retest evidence;
- retain this source and deployment identity;
- leave the Worker idle only if there is a near-term #220 conformance use;
- otherwise disable/remove **only this Worker** according to the recorded account inventory;
- do not dismantle the parked QOR proving stack;
- do not touch Empty Flagon Inn or Celestara.
