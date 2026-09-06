# ADR-025: Durable Decision Overwrites Require Explicit Authority

Status: Proposed

Date: 2026-08-12

## Context

Issues #137 and #138 expose a critical boundary in agent memory systems: agents may be able to detect contradiction, propose correction, and identify supersession candidates, but that does not automatically grant authority to overwrite durable decisions.

Durable decisions are different from ordinary observations. They may encode human approval, policy, governance posture, scope boundaries, or operational commitments. Allowing agents to quietly overwrite earlier durable decisions converts memory into an argument engine with a commit bit. That is not governance.

The repository already treats PAMA as the mutation authority boundary and conflict resolution as a separate component. This ADR clarifies that durable decision overwrite is a distinct authority event and must be resolved before commit.

## Decision

The system must distinguish agent-proposed supersession from committed durable decision overwrite.

Agents may propose corrections, supersession links, conflict candidates, replacement records, and supporting evidence. They must not independently overwrite, reverse, retire, or supersede prior durable decisions unless the applicable authority policy explicitly grants that mutation class for the affected scope.

For high-impact decisions or prior human-confirmed decisions, the default posture is human confirmation before overwrite unless a bounded policy explicitly delegates that authority.

Rejected, expired, or unapproved overwrite proposals remain auditable evidence and must not mutate durable decision state.

## Rationale

The useful work agents can do is proposing, gathering evidence, detecting contradiction, and presenting candidate resolutions. The risky work is granting those proposals durable authority without a valid policy basis.

This ADR preserves automation where it is valuable while preventing silent decision reversal. It also keeps the repository aligned with deterministic governance: probabilistic discovery may identify a possible correction, but deterministic authority controls whether durable state changes.

## Consequences

### Positive

- Durable decision overwrite becomes explicit and auditable.
- Human-confirmed decisions cannot be silently displaced by agent consensus.
- Agent proposals remain useful without becoming unauthorized mutation.
- PAMA retains control over mutation authority.
- Conflict resolution has a clear handoff into authority evaluation.

### Negative

- Some overwrites require human review, adding latency.
- Implementations must classify ordinary memory correction separately from durable decision overwrite.
- Delegated authority policies must be precise enough to avoid rubber-stamping.
- User interfaces and APIs must represent pending, approved, rejected, and expired overwrite proposals.

## Implementation notes

A conforming implementation should represent at least:

- proposal identifier;
- proposing actor;
- affected durable decision record;
- proposed replacement or supersession record;
- rationale and evidence basis;
- requested mutation class;
- authority policy used for evaluation;
- approval, rejection, or expiry status;
- approver identity where human confirmation is required;
- final commit receipt only when approved.

The proposal record may be durable evidence. It is not itself an overwrite unless approved under the applicable authority policy.

## Composition

This decision owns one boundary only: authority to replace what a durable decision says.

```text
conflict / drift / correction evidence
  -> overwrite proposal
  -> decision-specific authority resolution
  -> PAMA
  -> append-only supersession or refusal
```

Responsibility remains separated:

- **Conflict resolution (ADR-010)** may detect contradiction, rank hypotheses, and propose a resolution. It does not gain overwrite authority merely by selecting a preferred explanation.
- **Temporal causality (ADR-011)** preserves the prior decision and the explicit `supersedes` relationship. A successful overwrite creates a new historical/current relationship rather than editing history into agreement.
- **Lifecycle doctrine** determines whether the prior decision is current, superseded, reversed, disputed, or expired. A pending overwrite proposal does not change that lifecycle state.
- **PAMA (ADR-004/ADR-020)** remains the mutation-authority envelope. Satisfying a decision-specific approval requirement cannot weaken an independent PAMA block.
- **Observability (ADR-017)** preserves proposed, rejected, expired, approved, and committed outcomes as distinct evidence.
- **Shared-write coordination (ADR-024)** is orthogonal. Where multiple writers contend for the same durable decision, pre-write coordination may determine who gets to attempt the mutation; it does not grant the overwrite authority defined here.

## Current executable evidence

Issue #144 adds a bounded reference implementation and fixture family without changing this ADR's Proposed status.

The executable slice demonstrates:

- an agent overwrite proposal remains pending evidence and does not mutate the current durable decision;
- a commit attempt without authority fails closed;
- an exact human-confirmation grant can authorize the reference high-risk human-confirmed case, after which PAMA still evaluates the mutation;
- successful overwrite preserves the prior decision, appends a replacement, and records supersession evidence plus a decision receipt;
- an exact bounded delegated-policy grant can satisfy a low-risk overwrite of a decision that was not human-confirmed;
- agent consensus cannot replace human confirmation for a prior human-confirmed decision;
- stale proposal state, revoked/expired/not-yet-valid grants, proposal/target/scope/mutation/actor/risk mismatches, self-approval, and missing approval linkage on the replacement all fail without supersession;
- a valid human grant still cannot override an independent PAMA block;
- PAMA decision schema `1.1.0` adds the explicit `decision_overwrite` operation while historical operation records continue to use `1.0.0`.

Reference artifacts:

- `reference/agentmem_ref/memory/decision_overwrite.py`
- `reference/tests/test_decision_overwrite.py`
- `reference/tests/test_decision_overwrite_fixtures.py`
- `fixtures/durable-decision-agent-proposal.json`
- `fixtures/durable-decision-human-confirmed-overwrite.json`
- `fixtures/durable-decision-stale-overwrite.json`
- `fixtures/durable-decision-agent-collusion.json`
- `fixtures/durable-decision-delegated-low-risk-overwrite.json`
- `docs/profiles/durable-decision-memory-profile.md`
- `docs/33-pama-decision-table.md`
- `docs/15-memory-threat-model.md`

This evidence satisfies the implementation questions under #144 but does not automatically promote this ADR. Issue #144 explicitly excludes automatic ADR maturity changes; acceptance therefore remains a separate doctrine-governance decision.

## Validation and acceptance

This ADR should not advance beyond Proposed until the repository includes evidence for:

- an agent-proposed overwrite that remains pending or rejected without mutating durable decision state;
- a human-confirmed durable decision overwrite that creates append-only supersession evidence;
- an explicitly delegated low-risk overwrite case, if supported, with bounded policy evidence;
- negative-path coverage for unauthorized overwrite, stale evidence, silent decision reversal, and agent-collusion scenarios;
- documentation showing composition with PAMA, conflict resolution, temporal causality, lifecycle state, and audit events.

The current #144 reference slice is designed to satisfy those evidence prerequisites. A separate maturity review must still decide whether the evidence is sufficient to make ADR-025 canonical doctrine.

## Related

- #137
- #138
- #144
- ADR-004: PAMA Controls Mutation Authority
- ADR-010: Conflict Resolution Is a Separate Component
- ADR-011: Temporal Causality Is Required for Memory Evolution
- ADR-017: Memory Observability and Audit Events Are Required
- ADR-020: Probabilistic Discovery, Deterministic Governance
- ADR-023: Corrections Are Supersession, Not Deletion
- ADR-024: Shared Memory Writes Require Pre-Write Claims
