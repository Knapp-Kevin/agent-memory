# Governance Context Projection Profile

## Purpose

This profile defines a vendor-neutral, derived projection of Agent Memory state for governance consumers.

It exists to help policy, approval, and enforcement systems consume relevant memory without making Agent Memory core conform to any one governance product.

The projection is intentionally narrower than canonical memory and weaker than authority.

> **It tells a governance system what Agent Memory remembers that may matter to the decision. It does not tell the governance system what decision to make.**

## Architecture

```text
canonical Agent Memory
  identity / evidence / scope / lifecycle / rationale / outcome
        |
        v
Governance Context Projection
  minimized derived context
        |
        v
consumer adapter
  consumer vocabulary / API / policy semantics
        |
        v
governance decision / approval / enforcement
```

The canonical memory object remains the source of truth. The projection is rebuildable derived state.

## Ownership boundary

### Core Agent Memory primitives

The projection may consume generally useful primitives such as:

- memory identity and referenced subject/target
- provenance and evidence
- scope and isolation domain
- lifecycle and dispute state
- valid-time and event-time information
- correction, supersession, and revocation
- actor and authority context
- rationale/explanation with provenance
- outcome, rollback, incident, and execution evidence
- estimator provenance and uncertainty
- sensitivity and minimization constraints

### Projection semantics

The profile may derive:

- precedent references
- precedent polarity
- structured material conditions
- material differences
- freshness and validity status
- outcome/incident summaries
- authority-context references
- derivation and uncertainty metadata

### Consumer semantics

The profile does not own:

- DashClaw risk scores or verdict names
- AGT/ACS effects or policy identifiers
- OPA/Cedar policy expressions
- standing grants
- approval UX
- consumer retry behavior
- final allow/deny/escalate decisions

Those belong downstream.

## Required projection semantics

A projection conforming to V0.1 should preserve these concepts.

### Identity

```text
projection_id
projection_version
source_memory_refs
current_context_ref
```

`source_memory_refs` must point back to canonical Agent Memory identities or resolvable references. A projection without reconstructable source identity is not a valid governance context projection.

### Purpose

The projection declares a bounded `purpose`, such as `governance_decision_context`.

The purpose does not grant access. Existing scope, isolation, consent, and sensitivity policy still governs whether the projection may be produced or consumed.

### Scope

Projection carries a structured scope description or references sufficient to determine whether precedent crosses tenant/project/task/purpose boundaries.

Unknown scope is not equivalent to matching scope.

### Precedent

Each precedent entry contains at least:

```text
memory_ref
polarity
relationship
rationale_ref or bounded rationale summary when permitted
condition_refs / material_conditions
outcome_refs
validity
provenance
```

Candidate `polarity` values:

- `supportive`
- `cautionary`
- `contradictory`
- `neutral`

Polarity is not a vote count. One material cautionary precedent may outweigh many superficially similar supportive memories under downstream policy.

### Material conditions

Conditions are structured observations about why a precedent may or may not apply.

Examples:

```text
target_class = feature_branch
force = false
ci_state = current_green
credential_access = false
environment = staging
```

The projection may report comparison state such as:

- `match`
- `mismatch`
- `unknown`
- `not_compared`

A mismatch should name the condition rather than merely lower a similarity score.

### Freshness and validity

Projection preserves whether a precedent is current, stale, expired, superseded, revoked, disputed, or otherwise limited.

A stale or superseded precedent may remain useful historical evidence while being unsafe for current reliance.

### Outcome evidence

Where available, the projection may reference later outcomes:

- successful execution
- denied execution
- incident
- rollback
- revocation
- correction
- execution despite a governance gate

Outcome evidence remains evidence. Absence of a known incident is not proof of safety.

### Derivation

Projection declares how entries were selected:

```text
exact_identity
deterministic_condition_match
rule_based_retrieval
semantic_similarity
hybrid
```

If estimator-mediated selection is used, estimator identity/version and uncertainty must be preserved.

## No-decision rule

V0.1 deliberately has no field for:

```text
allow
deny
block
require_approval
standing_permission
risk_score
```

A consumer adapter may derive its own policy inputs from the projection. The projection itself remains evidence/context.

This is a structural control, not merely documentation advice: the V0.1 schema is closed to undeclared consumer-specific fields.

## Positive precedent example

```text
Current action:
  push feature branch

Retrieved precedent:
  prior approved feature-branch push

Material conditions:
  protected_target = false  -> match
  force = false             -> match
  ci_current = true         -> match

Outcome:
  completed successfully

Projection meaning:
  supportive context exists under matching conditions
```

The projection does not say to allow the action.

## Misleading near-match example

```text
Current action:
  force-push main

Retrieved precedent:
  prior approved feature-branch push

Material conditions:
  protected_target = false  -> mismatch (current = true)
  force = false             -> mismatch (current = true)
  ci_current = true         -> mismatch (current = false)

Projection meaning:
  prior positive precedent is materially non-equivalent
```

The downstream policy system may escalate or block. That consequence is not encoded by this profile.

## Negative precedent

Negative precedent includes denials, incidents, corrections, revocations, and other evidence that a superficially common action may have a dangerous subclass.

Projection must not erase negative precedent because supportive episodes are more numerous.

A later ranking implementation should preserve at least:

- polarity
- material condition relationship
- scope relationship
- validity
- outcome severity
- evidence provenance

before any aggregate relevance score is allowed to influence selection.

## Privacy and minimization

The default projection should prefer:

- memory/evidence references
- structured conditions
- categorical outcome summaries
- scoped fingerprints
- short bounded rationale summaries when policy permits

rather than copying raw memory content.

Sensitive rationale or content should remain referenced rather than embedded when the consumer can decide without the raw value.

## Conformance requirements

V0.1 conformance requires:

1. schema validation;
2. source-memory references present;
3. scope represented;
4. precedent polarity explicit;
5. material conditions represented with match/mismatch/unknown state;
6. derivation mode explicit;
7. estimator metadata present when derivation is probabilistic;
8. validity/freshness represented;
9. no final consumer verdict or standing permission field;
10. at least one supportive matching fixture and one misleading near-match / negative fixture.

## Evolution

Future versions may add richer relation and precedent structures only when they remain vendor-neutral and derive from generally useful Agent Memory primitives.

A consumer-specific need should first be implemented in that consumer's adapter. If repeated adapters expose the same genuine semantic gap, the profile may evolve. Core Agent Memory should change only when that gap proves to be a general memory primitive rather than an integration convenience.

## Related

- ADR-029
- ADR-028
- ADR-021
- [`../34-adapter-contracts.md`](../34-adapter-contracts.md)
- [`durable-decision-memory-profile.md`](durable-decision-memory-profile.md)
- #152
- #153
- #154
