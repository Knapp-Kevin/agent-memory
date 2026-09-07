# PAMA 1.3 Structural Delegation

Issue: #281  
Doctrine: ADR-032

PAMA decision `1.3.0` adds an explicit structural-impact binding for `domain_schema_mutation` so one narrowly defined S1 autonomous envelope can be represented without changing the meaning of historical 1.2.0 decisions.

Compatibility remains cumulative for the domain-schema path:

```text
1.2.0
  domain_schema_mutation is conservatively review / external-verification gated

1.3.0
  domain_schema_mutation binds an exact deterministic structural-impact record
  S1 may be allow_with_ledger only inside a versioned deterministic delegation
  S2/S3 remain human-authorized or blocked
```

PAMA 1.2 remains valid historical evidence. A 1.2-only consequential consumer must reject a 1.3 decision it cannot interpret.

## Structural classifier

The reference classifier is versioned independently from estimator evidence:

```text
classifier: agent-memory-structural-impact@1.0.0
policy:     agent-memory-structural-autonomy@1.0.0
```

The impact record is `schemas/structural-mutation-impact.schema.json`.

It binds at least:

- current/proposed schema identity and version;
- structural layer and change kind;
- semantic-preservation posture;
- migration and information-loss posture;
- historical-interpretation posture;
- scope, authority, and isolation impact;
- affected-memory bound;
- dependencies and incompatible/live dependencies;
- reversibility and rollback reference;
- rebuild/residue obligations;
- exact state and dependency snapshot digests;
- source evidence;
- estimator identity/version/confidence as evidence only;
- classifier/policy identity and version;
- deterministic S0-S3 classification.

Estimator confidence is not an input to the structural class or authority outcome.

## S0

S0 remains unchanged-semantic derived/rebuild maintenance.

```text
S0 != domain_schema_mutation
```

The classifier can identify S0 so a module cannot relabel a semantic mutation as a harmless rebuild, but PAMA 1.3 refuses to serialize S0 as `domain_schema_mutation`. Derived maintenance remains governed through the maintenance/currentness lifecycle.

## S1 autonomous envelope

The initial reference S1 delegation is intentionally narrow.

An autonomous S1 candidate must prove all configured conditions, including:

- application/domain layer;
- optional additive extension;
- existing and historical interpretation preserved;
- no migration;
- no information loss;
- no scope widening;
- schema scope within the configured S1 policy;
- no authority widening;
- isolation preserved;
- affected-memory count within the configured bound;
- no incompatible dependencies;
- reversible or versioned-revocable posture;
- explicit rollback reference;
- current state/dependency snapshot digests still match the impact analysis.

The default reference policy currently permits `project`, `application`, and `local` schema scopes and bounds S1 affected memory to 1000 records. These are **reference policy values**, not universal doctrine thresholds.

A qualifying S1 decision may resolve to:

```text
outcome: allow_with_ledger
selection_mode: deterministic
structural_class: S1
```

It must not carry human review references merely to disguise an autonomous path.

## S2

Semantic reinterpretation, migration-bearing changes, possible/unknown information loss, incompatible dependencies, or unproven historical interpretation are S2 by default.

S2 is not autonomous under this profile. It remains review-required, with high/critical risk preserving the stronger external-verification floor. A later allowed decision must preserve explicit review references and `selection_mode = human | external`.

## S3

Scope widening, authority/governance-bearing meaning, isolation change, irreversible change, certain information loss, or destructive retirement with live dependencies are S3 pressure.

S3 is never autonomously committed by this profile. Existing PAMA floors remain controlling and may block the request entirely.

## Freshness and dependency drift

Structural authorization is bound to:

```text
state_digest
dependency_digest
```

Authorization fails if either digest no longer matches the impact analysis. A previously correct classifier result is not authority for a changed state.

This prevents:

- stale blast-radius analysis;
- newly introduced consumers being ignored;
- a proposal being authorized after its target schema changed;
- deterministic classification from becoming an indefinitely reusable capability token.

## Lifecycle

The reference lifecycle keeps the following states distinct:

```text
proposed
  -> authorized
  -> active
  -> superseded
  -> retired
```

Authorization and activation are separate. Retirement is allowed only after supersession and only when live dependencies and pending residue obligations are empty.

This follows ADR-032's preference for supersession before retirement and prevents destructive cleanup from being inferred from successful activation of a successor.

## PAMA floors remain controlling

PAMA 1.3 does not bypass:

- actor-authority reconstruction;
- self-approval prohibition;
- target-class floors;
- downstream-authority floors;
- scope-expansion floors;
- isolation-domain requirements;
- reversibility escalation;
- evidence requirements.

The S1 structural policy supplies a versioned **base cell** only after deterministic structural eligibility is proven. Common PAMA floors are then applied normally.

## Evidence

Executable surfaces:

- `schemas/structural-mutation-impact.schema.json`
- `schemas/pama-decision.schema.json`
- `reference/agentmem_ref/memory/structural_mutation.py`
- `reference/agentmem_ref/memory/structural_pama.py`
- `reference/tests/test_structural_mutation_governance.py`
- `reference/run_structural_mutation_governance.py`
- `.github/workflows/structural-mutation-governance.yml`

The exact-head characterization includes S0, autonomous S1, review-required S2, destructive/authority-bearing S3, confidence-independence, stale-state rejection, dependency-drift rejection, lifecycle retirement gates, and historical PAMA compatibility.

## Non-goals

This profile does not:

- make all additive schema changes autonomous;
- make S0 a domain-schema mutation;
- let confidence choose structural class;
- perform provider-specific migrations;
- make affected-memory count a universal risk metric;
- allow stale impact analysis to authorize a later state;
- retire a schema with live dependencies or residue;
- rewrite historical PAMA 1.2 decisions.
