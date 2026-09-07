# Scoped Security Finding Evidence Profile

Status: V0.1 reference profile for #198.

This profile defines a vendor-neutral evidence boundary for adversarial scanners, security scanners, benchmarks, and related negative-evidence producers.

The first two reference families are intentionally different:

- **NVIDIA garak v0.16.0**, exact commit `dbe4515d12664f2e34ac2cea295f055c22fe82b4`, behavioral red-team/probe evidence;
- **Snyk Agent Scan v0.5.17**, exact commit `ea959964ce4728426fca9fa78c9e7809b972f313`, agent/MCP/skill supply-chain and configuration evidence.

The purpose is not to make Agent Memory speak either scanner's ontology. The purpose is to preserve what was observed, under what exact conditions, without converting scanner output into authority.

## Core boundary

```text
scanner hit
!= universal vulnerability fact

no hit
!= proof of safety outside tested scope

benchmark / scanner score
!= runtime incident

security finding
!= standing policy

reproduction
strengthens evidence
!= creates authority

scanner identity/version
!= memory authority
```

Every normalized V0.1 finding fixes these nonclaims:

```text
authority_effect = none
universal_vulnerability = not_established
safety_claim = not_established
standing_policy = not_established
memory_admission = not_established
certification_claim = none
```

## Generic evidence contract

A normalized finding preserves:

```text
finding family
scanner/tool identity
exact scanner version and source commit
adapter id/version
source contract status
target identity + configuration ref
scope / tenant / project / environment
check / probe / case identity
evaluator / detector identity
sample size / repetitions / seed where meaningful
result status + verdict
source-native counts or metric where semantics are pinned
reproduction state
finding lifecycle state
candidate classification
scanner execution context
sandbox state
consent state
scanner privilege ref
raw evidence ref/digest
known limitations
prior/remediation/rescan/conflict lineage
exact scope binding status
```

The schema does not define a generic vulnerability truth score.

## Garak pinned adapter

V0.1 pins garak `v0.16.0` because that release explicitly changed `report.jsonl`.

The adapter consumes the pinned `entry_type = eval` fields:

```text
probe
detector
passed
fails
total_evaluated
optional confidence bounds
```

Garak's evaluator contract defines `passed` and `fails` under the exact probe/detector execution. V0.1 preserves those counts directly.

It also exposes a source-native `garak_pass_rate` only as scanner evidence:

```text
passed / total_evaluated
```

That metric is not Agent Memory confidence, truth, authority, certification, or a universal risk score.

V0.1 verdict mapping is intentionally bounded:

```text
total = 0                  -> unknown
fails = 0                  -> no_hit
passed = 0 and fails > 0   -> hit
passed > 0 and fails > 0   -> mixed
```

A hit/mixed result is an observed failure under the exact target, configuration, probe, detector, and sampling conditions. A no-hit result says only that no failure was observed in that bounded evaluation.

## Snyk Agent Scan projection adapter

Snyk Agent Scan `v0.5.17` is pinned as the second materially different family.

Its upstream CLI/JSON shape is not adopted as Agent Memory core semantics. The adapter receives a bounded Agent Memory-facing projection and records:

```text
source_contract_status = experimental_projection
```

Upstream field names, issue codes, severity labels, and response structure may evolve without requiring the generic Agent Memory schema to evolve.

### Active scanning is evidence

Snyk documents that scanning stdio MCP configurations can execute the commands defined in those configurations.

Therefore V0.1 preserves separately:

```text
target_execution = observed | possible | not_observed | not_applicable | unknown
sandbox = isolated | not_isolated | not_applicable | unknown
consent = granted | declined | bypassed | not_required | unknown
scanner_privilege_ref
```

A scanner is not assumed to be a passive observer merely because its output is called a finding.

A declined scan must remain:

```text
result_status = declined
verdict = not_run
finding_state = not_run
```

It cannot fabricate a finding or proof of safety.

## Scope and environment binding

Target identity alone is not enough to generalize a result.

V0.1 compares, when expected:

```text
target_ref
scope_ref
tenant_ref
project_ref
environment_ref
```

A matching component/tool under another tenant, project, or environment is a binding mismatch. Scanner names, target names, configuration similarity, or repeated findings do not repair that mismatch.

## Finding lifecycle and append-only lineage

V0.1 supports finding states including:

```text
observed
reproduced
not_reproduced
nondeterministic
triaged
remediation_proposed
remediation_applied
rescanned
resolved
residual
disputed
not_run
```

Reproduction state is preserved separately because repeated observation and remediation lifecycle are not the same fact.

Every later record may preserve:

```text
prior_finding_refs
remediation_refs
rescan_refs
conflict_refs
```

The original finding is not overwritten.

Examples:

```text
observed hit
-> reproduced
```

creates a new evidence record referencing the original. It strengthens the reproduction evidence without creating authority.

```text
remediation_applied
+ no rescan
```

does not become `resolved`.

```text
original hit
+ later no_hit rescan
```

preserves both records and may explicitly reference the conflict/prior lineage. The later no-hit result still does not establish universal safety.

## Conflicting findings

Different scanners, detector versions, target configurations, or repeated runs may disagree.

That disagreement is representable rather than collapsed:

```text
finding A
<-> conflict_refs
finding B
```

The generic schema does not select a winner by scanner reputation, severity label, or recency alone.

## Security evidence depth

P2-B reuses the D/F/H/R/P model from #196.

The exact-head scanner-adapter evidence report is emitted by:

```text
reference/run_security_finding_depth.py
```

V0.1 claims:

```text
garak adapter        = D + F + H
Snyk projection      = D + F + H
R                    = explicitly unproven
P                    = explicitly unproven
```

Why no R?

The behavioral harness executes the Agent Memory adapters against pinned fixtures/projections. It does not launch a live garak scan or a live Snyk Agent Scan target. Fixture execution therefore earns H, not R.

No composite score is emitted.

## Privacy and minimization

Security evidence is often sensitive enough to become a new attack surface if copied casually.

V0.1 defaults to refs/digests and does not require copying:

- raw attack prompts;
- generated exploit payloads;
- secrets or credentials;
- full scanner dumps;
- hidden reasoning;
- complete target configuration;
- experimental scanner response blobs.

The adapter may inspect source output at the boundary long enough to produce the stable projection. The normalized record is intentionally smaller.

## Required negative paths

The executable V0.1 suite covers:

1. garak hit/mixed result remains non-authoritative;
2. garak no-hit result does not establish safety;
3. garak version/record-contract drift is rejected;
4. Snyk experimental raw fields remain adapter-local;
5. declined Snyk MCP scan remains not-run and cannot claim execution;
6. partial and target-unavailable scans remain explicit;
7. active MCP scanning preserves execution/sandbox/consent context;
8. cross-tenant/environment binding fails closed;
9. reproduction creates append-only lineage without authority escalation;
10. remediation without rescan does not become resolved;
11. rescan/conflicting findings preserve prior/conflict references;
12. two materially different families share one generic interpretation contract.

## Deployment profiles

### L: local

Active scanner execution may expose local files/configuration or start configured MCP commands. Consent and sandbox evidence are important even without enterprise identity infrastructure.

### T: team / multi-tenant

Tenant/project/environment bindings prevent one workspace's finding from becoming a universal claim about the same named component elsewhere.

### E: enterprise

Findings may feed incident/remediation workflows, but they remain scoped evidence candidates and do not create standing policy automatically.

### H: high assurance

Exact scanner/tool/source versions, raw evidence custody, test conditions, execution context, reproduction lineage, conflicts, and evidence-depth gaps must remain reconstructable.

## V0.1 non-claims

V0.1 does not claim:

- garak or Snyk Agent Scan is required by Agent Memory;
- one scanner result proves a system vulnerable or safe in all contexts;
- scanner severity or score is an Agent Memory truth metric;
- reproduced findings create policy authority;
- remediation is effective without rescan evidence;
- a scanner result is a production incident;
- adapter tests are live-scanner runtime evidence;
- any external scanner mapping constitutes certification.

## Stop line

Do not expand this slice into:

- vulnerability-management product features;
- automatic standing policy creation;
- scanner orchestration;
- raw finding dump retention by default;
- PyRIT or CyberSecEval support;
- generic adoption of experimental scanner field names;
- a scalar security score.
