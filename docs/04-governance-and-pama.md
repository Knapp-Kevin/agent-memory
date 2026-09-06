# Governance and PAMA

## Purpose

PAMA defines mutation authority for agentic memory systems.

The central question is not whether an agent can change memory. The central question is whether it is allowed to change memory, under what scope, with what evidence, and with what rollback path.

PAMA also defines the boundary between uncertain inference and governed consequence.

**Probabilistic or learned systems may estimate confidence, trust, relevance, contradiction, sensitivity, utility, or risk. PAMA determines what those estimates are allowed to change.**

## Native doctrine and provenance

PAMA means **Proportional Adaptive Mutation Authority**.

PAMA is **native Agent Memory doctrine authored by Kevin R. Knapp**. It is not an external source system or dependency that Agent Memory imports from elsewhere.

The systems-agnostic foundation is summarized in [`pama/README.md`](pama/README.md). This document specializes that foundation for memory lifecycle, durable state, correction, deletion, sharing, policy, and action boundaries.

External standards, research, and implementation systems may support, challenge, align with, or implement PAMA. They do not define its authorship or become its source of authority.

## Foundational PAMA thesis

> **Adaptation should be broadly available to authorized agents. Authority to make a mutation durable, influential, shared, or action-enabling should increase in proportion to the mutation's consequence.**

PAMA preserves four separations:

```text
adaptation != authority
memory != procedure
procedure != permission
permission != governance
```

An agent may observe, infer, propose, or learn without automatically receiving authority to apply a durable or consequential change.

A remembered fact or preference does not automatically become an executable workflow.

A validated procedure does not automatically authorize the agent to execute it.

Permission to act does not authorize an agent to expand, weaken, or redefine governance itself.

The associated review rule is:

> **Review should be applied at promotion and consequence boundaries, not at every observation boundary.**

This is why PAMA is proportional rather than approval-heavy. Low-risk reversible learning should not turn a human into the throughput bottleneck. High-impact mutation should attract stronger evidence, validation, review, authorization, and monitoring.

## PAMA dimensions

PAMA evaluates several dimensions that must not be collapsed into one score.

### Mutation target classes

Target class describes **what kind of state is being changed**.

| Class | Target type | Examples | Default posture |
|---|---|---|---|
| **M0** | Execution-local context | current-session correlation, temporary intent interpretation, local retrieval hint | transient; expire automatically |
| **M1** | Low-risk personal preference | formatting, terminology, view, pacing | tentative, visible, reversible |
| **M2** | Operational association | project routing, recurring task association, workflow suggestion | evidence-backed; recommendation influence |
| **M3** | Reusable procedure or capability | validated checklist, repair sequence, reusable workflow | validation and promotion controls |
| **M4** | Shared fact or identity-bearing state | relationship, entitlement, commitment, permission-affecting fact | authoritative evidence and controlled review |
| **M5** | Governance, security, or autonomous-action authority | policy exemption, trust elevation, send/deploy/delete authority | explicit authorization; no self-approval |

### Lifecycle strength

Lifecycle strength describes how established retained state is:

```text
Observed -> Tentative -> Reinforced -> Promoted -> Canonical
                   \-> Decaying -> Archived / Deprecated / Blocked
```

Lifecycle strength does not itself grant downstream authority.

### Downstream authority classes

Downstream authority describes **what the retained mutation is permitted to influence**.

| Class | Authority | Meaning |
|---|---|---|
| **A0** | Retrieval only | inspection or context recall |
| **A1** | Recommendation influence | rankings, suggestions, routing, planning |
| **A2** | Draft generation | drafts for review, no execution |
| **A3** | Local workflow mutation | authorized internal state changes |
| **A4** | External action | messages, deployments, purchases, deletions, bookings, provider state |
| **A5** | Governance change | privileges, policy, trust, enforcement, future autonomy |

A mutation can be strongly validated and still have a low authority ceiling. Reliability does not create permission.

## Memory mutation operations

Agent Memory additionally classifies **the operation being requested**. These are operational mutation types, not replacements for PAMA's M0-M5 target classes.

| Operation | Description | Default authority |
|---|---|---|
| Runtime assembly | Build context from existing memory | allowed with audit |
| Score adjustment | Update saturation, confidence, or decay pressure | allowed with ledger when low risk |
| Link creation | Add graph relation between memory units | allowed if evidence-backed |
| Link deletion | Remove graph relation | require review unless low risk |
| Correction | Amend disputed memory | require provenance and ledger |
| Promotion | Move memory toward durable state | require certification gate |
| Crystallization | Make memory canonical or exact-address durable | require explicit authority |
| Pruning | Remove from active recall | require reversible tombstone unless ephemeral |
| Permanent deletion | Intentionally make recovery unavailable | explicit high-consequence authority and deletion scope required |
| Scope expansion | Share memory with broader actor or tenant scope | explicit authority appropriate to target scope |
| Policy mutation | Change governance rules | require human or equivalently authoritative approval |

A compliant decision therefore considers at least:

```text
target_class
lifecycle_strength
requested_operation
downstream_authority
risk
scope
reversibility
evidence
policy
actor_authority
```

The operation/risk decision table in [`33-pama-decision-table.md`](33-pama-decision-table.md) is an Agent Memory specialization of this multidimensional PAMA model, not the whole of PAMA.

## Authority outcomes

PAMA should return one of these outcomes:

```text
allow
allow_with_ledger
require_review
require_external_verification
block
```

Implementations may add outcomes such as `abstain`, `quarantine`, or `collect_more_evidence` when useful, but every outcome must have defined consequence semantics.

## Authority resolution invariant

For a fixed set of committed inputs, current state, and policy version, PAMA must produce a **deterministic or formally bounded authority envelope**.

This does not require all upstream inputs to be deterministic.

It requires that:

1. the policy knows which inputs are estimates;
2. their provenance and uncertainty are inspectable;
3. the estimator cannot grant itself authority;
4. prohibited actions remain prohibited regardless of confidence;
5. any stochastic behavior after authorization selects only among already-permitted actions; and
6. the resulting authority decision can be reconstructed from its receipt.

## Risk classes

Risk remains an operational dimension in Agent Memory and composes with PAMA target and authority classes.

| Risk | Examples | Required handling |
|---|---|---|
| Low | temporary context, low-impact links, ephemeral cache decay | allow with normal ledger |
| Medium | task memory, project notes, reusable summaries | allow with evidence and reversible correction |
| High | user preferences, security policy, durable decisions, code mutation plans | require review or certification |
| Critical | identity, credentials, compliance, permanent deletion, cross-tenant scope expansion, safety boundaries | require explicit human or equivalently authoritative approval |

## Consequence proportionality

Governance strength should rise with consequence, not merely with estimator confidence.

Relevant dimensions include:

```text
target_class
lifecycle_strength
downstream_authority
reversibility
persistence horizon
sensitivity
scope / tenancy
blast radius
canonicality
authority level
dependency fan-out
ability to destroy evidence
ability to alter future governance
```

A low-confidence, reversible cache decision may still be acceptable.

A high-confidence proposal for permanent deletion may still require explicit review.

## PAMA evaluation inputs

```text
memory_state
target_class
lifecycle_strength
mutation_type
requested_downstream_authority
risk_class
actor
agent_charter_version
source_authority
evidence_quality
saturation
confidence
contradiction_pressure
reversibility
blast_radius
certification_status
user_approval_state
policy_scope
estimator_refs
estimator_versions
calibration_refs
uncertainty_summary
estimator_disagreement
out_of_distribution_signal
requested_scope_change
```

PAMA should distinguish required inputs from optional advisory signals. Missing advisory signals may reduce decision quality. Missing required authority inputs must not be silently guessed for consequential actions.

Unknown consequence must not be converted into presumed safety.

## Proportional handling lanes

PAMA concentrates review where influence and consequence increase.

| Lane | Typical use | Core control |
|---|---|---|
| **1. Transient automatic** | M0 context and narrow interpretations | no durable authority or external effect |
| **2. Tentative low-risk retention** | M1 and selected recommendation-only M2 | visible, removable, scoped |
| **3. Evidence-backed reinforcement** | meaningful but reversible M2 | evidence, correction, conflict checks |
| **4. Promotion and review** | M3, shared knowledge, meaningful workflow behavior | validation, versioning, authority ceiling, rollback |
| **5. Restricted authority** | M4/M5 effects involving external action or governance | explicit authorized review, no self-approval, fail closed when authority is ambiguous |

Human attention is a scarce governance resource. PAMA spends it where a mutation becomes durable, shared, action-enabling, identity-bearing, security-relevant, or governance-changing.

## Promotion rule

Promotion requires more than saturation.

```text
can_promote =
  identity_resolved
  and provenance_present
  and saturation >= candidate_threshold
  and trap_class_check == pass
  and pama_outcome in [allow, allow_with_ledger, require_review]
```

This is a simplified gate, not a claim that a point threshold is sufficient.

If PAMA returns `require_review`, the memory may enter Pending Verification but must not crystallize.

If estimator uncertainty, disagreement, drift, or scope invalidates the confidence of a consequential promotion proposal, PAMA may return:

```text
require_review
require_external_verification
block
```

rather than inferring permission from the score.

## Crystallization rule

```text
can_crystallize =
  can_promote
  and certification_status == pass
  and pama_outcome in [allow, allow_with_ledger]
  and scope_defined
  and dispute_status == clear
```

Crystallization should bind to the evidence set, policy version, estimator context, authority record, and scope under which it was approved.

## Capability authority ceiling

Reusable capability is a first-class PAMA concern.

A procedure that is repeatedly successful may become a validated capability artifact. It must still declare the maximum downstream authority it can influence.

Examples:

```text
may retrieve and recommend only
may draft but not send
may update bounded internal workflow state
may not execute external tools without separate authorization
```

> **Validation can justify trust in a capability. It does not automatically grant permission to use that capability autonomously.**

## Bounded stochastic action

PAMA does not require every downstream choice to be deterministic.

If governance produces a permitted set such as:

```text
permitted_actions = [
  store_ephemeral,
  request_more_evidence,
  defer
]
```

a planner may choose deterministically or stochastically among those actions if policy allows.

It may not sample from:

```text
[
  store_ephemeral,
  request_more_evidence,
  defer,
  crystallize_without_certification
]
```

and then claim the unsafe action was merely a probabilistic outcome.

Randomness does not create permission.

## Anti-patterns

### Repetition as authority

Wrong:

```text
many accesses -> crystallized
```

Correct:

```text
many meaningful accesses -> possible saturation increase -> candidate -> certification -> governed crystallization
```

### Confidence as authority

Wrong:

```text
model says it confidently -> durable memory
```

Correct:

```text
model confidence -> evidence signal -> calibrated scoring -> governance -> verification path
```

### Procedure as permission

Wrong:

```text
validated procedure -> autonomous execution
```

Correct:

```text
validated procedure -> governed capability -> authority ceiling -> separately authorized execution
```

### Summary as authority

Wrong:

```text
summary says X -> source can be discarded
```

Correct:

```text
summary says X -> source refs retained -> provenance survives compression
```

### Determinism as correctness

Wrong:

```text
fixed threshold produced same answer twice -> safe decision
```

Correct:

```text
reproducible decision + calibrated inputs + valid policy + appropriate consequence controls -> auditable governed decision
```

### Probabilistic utility as deletion authority

Wrong:

```text
predicted_future_utility < 0.05 -> permanently delete
```

Correct:

```text
low predicted utility -> deletion candidate -> retention/dependency/privacy policy -> authorized deletion mode
```

## Adaptive authority

PAMA is proportional and adaptive.

Authority may increase when:

- memory is low risk;
- mutation is reversible;
- evidence is strong;
- policy scope is narrow;
- prior similar mutations succeeded;
- user has delegated authority explicitly; and
- estimator calibration is valid for the current scope.

Authority must decrease or escalate when:

- contradiction pressure rises;
- source authority weakens;
- trap-class behavior appears;
- mutation blast radius grows;
- certification is missing or expired;
- system confidence exceeds evidence quality;
- estimator disagreement is material;
- estimator calibration is stale or out of scope;
- a requested mutation expands sharing or tenancy scope; or
- the action destroys rollback, evidence, or future governance options.

## Uncertainty handling

PAMA should distinguish at least:

```text
epistemic uncertainty: uncertainty about the content or model
aleatoric uncertainty: irreducible variability/noise where relevant
policy uncertainty: policy is missing, ambiguous, conflicting, or version-misaligned
authority uncertainty: actor permission cannot be reconstructed
scope uncertainty: target user, tenant, or domain is unclear
```

Not all uncertainty should be handled the same way.

For example:

- low-risk epistemic uncertainty may still permit an ephemeral write;
- policy uncertainty on a high-impact mutation should block or escalate;
- authority uncertainty must never be resolved by estimator confidence; and
- scope uncertainty should prevent broad sharing until resolved.

## Fail-safe behavior

For high or critical consequence actions, PAMA should fail closed or escalate when required governance state cannot be reconstructed.

Examples:

```text
policy version missing -> block / require review
actor authority unresolved -> block
scope ambiguous for cross-tenant sharing -> block
certification reference invalid -> block crystallization
estimator outside calibration scope -> require verification for consequential promotion
```

Low-risk, reversible operations may use explicitly defined degraded modes if policy permits them.

## Audit requirements

Every mutation decision should record:

```text
mutation_id
memory_id
actor
agent_charter_version
target_class
lifecycle_strength
requested_mutation
requested_downstream_authority
pama_inputs
estimator_refs
estimator_versions
calibration_refs
uncertainty_summary
pama_outcome
permitted_action_set
selected_action
selection_mode
policy_refs
policy_version
evidence_refs
approval_refs
before_state
after_state
rollback_path
timestamp
```

`selection_mode` should identify whether a permitted downstream choice was deterministic, stochastic, human-selected, or externally determined.

## Replay requirement

A decision receipt should allow an auditor to answer:

1. What did the uncertain components estimate?
2. Which estimator and calibration versions produced those estimates?
3. Which target class, lifecycle strength, requested operation, and authority ceiling were evaluated?
4. Which policy version interpreted them?
5. What actions were prohibited?
6. What actions were permitted?
7. Which permitted action was selected and how?
8. What state changed?
9. Could the change be rolled back?

Exact replay of a stochastic estimator is not always possible or necessary. Exact reconstruction of **authority and consequence** is required.

## Runtime enforcement

PAMA should be enforced at the boundary where the system changes memory or behavior, not merely where it explains memory.

Good enforcement points:

- Vault write boundary;
- crystallization gate;
- graph mutation API;
- agent action planner;
- reusable capability invocation boundary;
- code governance layer;
- correction workflow;
- pruning workflow;
- deletion workflow; and
- scope-sharing boundary.

## Required adversarial cases

PAMA conformance should eventually include:

- high-confidence false memory requesting durable promotion;
- threshold jitter near promotion boundary;
- estimator disagreement about sensitivity;
- high semantic relevance from the wrong tenant;
- stochastic planner offered both permitted and prohibited actions;
- permanent deletion proposed from uncertain future utility;
- policy-version drift after a prior authorization;
- missing authority record during replay;
- concurrent conflicting mutation requests;
- unsafe multi-memory composition that was not visible at individual write time;
- validated M3 capability attempting to exceed its A1/A2 authority ceiling; and
- M5 governance mutation disguised as a lower-risk operational update.

## Doctrine

PAMA is not a memory score.

PAMA is not an external dependency of Agent Memory.

PAMA is the authority architecture that decides whether a proposed adaptive mutation is allowed and how much consequence it may carry.

Probability may inform PAMA. Probability does not become PAMA.

**Learning may be broad. Consequence remains governed.**
