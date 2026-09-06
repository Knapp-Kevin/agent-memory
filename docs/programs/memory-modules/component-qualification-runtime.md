# Component Capability Qualification Runtime

Status: **Implementation evidence / #300**

Tracks: #300, #280, #293, #282

## Purpose

This document describes the executable component-capability qualification surface established by PR #302 and completed by PR #307.

It is the runtime counterpart to [`component-adapter-qualification-contract.md`](component-adapter-qualification-contract.md).

The executable contract now covers both successful provider behavior and bounded failure/fallback behavior:

```text
component declaration
  != qualification evidence

provider-native execution
  -> preserved raw artifact
  -> provider-neutral factual normalization
  -> profile checks
  -> version-bound qualification record
  -> earned capability maturity

selected provider becomes unavailable
  -> real failure evidence
  -> explicit configured fallback evaluation
  -> one equivalent fallback OR explicit unavailable
```

Qualification and fallback remain evidence/routing surfaces only. Neither grants Agent Memory mutation, structural, recall-admission, or action authority.

## Machine-readable evidence surface

Schema:

`schemas/component-capability-qualification.schema.json`

Current schema version:

`1.1.0`

Reference implementations:

- `reference/agentmem_ref/contracts/qualification.py`
- `reference/agentmem_ref/contracts/component_failure_probe.py`
- `reference/agentmem_ref/contracts/component_fallback.py`
- `reference/agentmem_ref/crg/code_graph_qualification.py`

The qualification subject binds:

```text
component_id
component_version
exact implementation_ref
capability_id/version
adapter_id/version
qualification_profile_id/version
```

Runtime applicability additionally binds:

```text
configuration digest
fixture identity + digest
material dependency refs
runtime refs
```

The deterministic applicability digest is computed over the exact subject and runtime identity. A changed component, adapter, profile, fixture, dependency/runtime identity, or material configuration does not silently inherit prior qualification.

Silence is not compatibility.

## Maturity progression

A qualification record separates:

```text
maturity_before
profile_maturity_ceiling
earned_maturity
qualification_current
```

A provider at `runtime_wired` may earn `evidence_proven` when the profile proves the required behavior. It may not exceed the profile ceiling.

A runtime route may rely on qualification only while the exact applicability identity remains current.

The first CodeGenome/Graphify qualification remains bounded to the maturity earned by its profile. A result for `code_graph_traversal` does not promote vector retrieval, GraphRAG, MCP, confidence fusion, procedural memory, or any unrelated capability.

## Provider-neutral adapter result

Reference type:

`AdapterResult`

It binds or preserves equivalents of:

```text
exact qualification subject
operation
runtime identity
input refs
raw provider artifact refs
normalized factual result refs
currentness posture
failure result
trace/correlation ref
authority effect
```

Raw provider evidence is mandatory and is not replaced by normalization.

Each adapter result exposes:

`authority_effect = none`

The qualification record preserves the same invariant.

Schema 1.1.0 requires the adapter-result evidence needed to reconstruct both successful and unavailable-provider outcomes rather than inferring them from a summary flag.

## First capability profile

Profile:

`code-graph-traversal-currentness@1.1.0`

Providers:

- CodeGenome `43a6b7147ec78ec5c616723fa1dd30f342174860`
- Graphify `v0.9.43`, commit `7281f27eac568f77f50910f59f84543458f5dfd1`

The CodeGenome pin was deliberately advanced from the planning revision `d2578729a46d495369bd7613845002d50cf20f4c` after the qualification fixture exposed a remaining cross-file semantic-resolution collision. CodeGenome #12 / PR #13 repaired file-scoped symbol and caller-span resolution. The qualification advanced the exact pin rather than weakening the fixture.

The workflow validates exact source refs before execution and verifies source-rights files from those exact revisions.

The profile normalizes only shared factual call-graph behavior. It does not force providers to emit the same native schema. Graphify's NetworkX node-link evidence uses native `links`; the normalizer preserves that shape and accepts `edges` only as a compatibility fallback.

## Adversarial fixture

Fixture root:

`reference/fixtures/component-qualification/`

The fixture intentionally separates target-file identity from line identity:

```text
v1 main.rs
  leaf              starts line 1
  middle            starts line 5
  top               starts line 9

v1 decoy.rs
  middle            starts line 5
  decoy_leaf        starts line 12

v2 main.rs
  middle            starts line 5
  top               starts line 9
  replacement_leaf  starts line 13
```

The duplicate `middle` start line means a provider cannot pass target resolution by line span alone. Distinct leaf identities make decoy contamination and stale v1 edges observable.

## Currentness posture

The first profile uses an explicit **full rebuild** between v1 and v2.

```text
full rebuild proven
!= incremental refresh proven
```

The evidence establishes:

- v1 `middle -> leaf` exists;
- v2 `middle -> replacement_leaf` exists;
- the v1 relationship is not reported as current after the v2 rebuild;
- decoy-file relationships remain isolated;
- v1 raw artifacts remain preserved as historical evidence.

A later incremental update path requires its own qualification evidence.

## Real provider-unavailable evidence

Provider outage is exercised against the exact runtime path, not synthesized from a test flag.

For each provider the evidence workflow:

1. builds or installs the exact qualified provider;
2. temporarily moves the executable out of its configured path;
3. invokes that exact missing path through `run_component_failure_probe.py`;
4. preserves the resulting operating-system `FileNotFoundError` as raw evidence;
5. normalizes the bounded result to:

```text
failure_result = provider_unavailable
currentness = unavailable
authority_effect = none
```

The probe fails if the executable actually runs, exits for a different reason, or times out. A separate negative unit test uses a real runnable Python executable and proves it cannot be laundered into `provider_unavailable`.

Therefore:

```text
configured provider path missing
  -> provider_unavailable evidence

provider returned an error
  != automatically provider_unavailable

provider timed out
  != automatically provider_unavailable
```

Different failure classes require their own evidence rather than being collapsed for convenience.

## Explicit no-weaker fallback

Reference evaluator:

`evaluate_explicit_fallback()`

Fallback is considered only after the already-selected primary has a real failure result. It considers only providers explicitly listed in configuration.

A candidate is refused when it changes or weakens any required equivalent of:

- capability identity/version;
- capability maturity;
- canonical/derived state posture;
- scope/isolation posture;
- failure posture;
- authority effect;
- qualification profile identity/version;
- qualification currentness;
- earned maturity;
- runtime source-rights posture.

The outcomes are deliberately narrow:

```text
no configured fallback
  -> unavailable / fallback_not_configured

configured candidates but none equivalent
  -> unavailable / no_equivalent_fallback

exactly one equivalent configured fallback
  -> fallback_selected / explicit_equivalent_fallback

more than one equivalent configured fallback
  -> unavailable / ambiguous_equivalent_fallbacks
```

There is no registration-order or first-match escape hatch.

Every fallback decision exposes:

`authority_effect = none`

Fallback changes the provider used to attempt a capability. It does not weaken governance requirements and cannot authorize a consequence.

## No product winner

The matched result preserves:

```text
both_passed: <boolean>
winner: null
authority_effect: none
unrelated_capabilities_promoted: []
```

This profile answers whether materially different providers satisfy the same bounded qualification checks. It does not declare a universal product winner.

## CI surfaces

Focused contract CI:

`.github/workflows/component-qualification-foundation.yml`

Real-provider evidence CI:

`.github/workflows/component-qualification-evidence.yml`

The real-provider workflow now:

1. runs schema, qualification, fallback, failure-probe, and normalizer tests;
2. fetches and builds exact CodeGenome source;
3. executes CodeGenome v1/v2 truth and currentness checks;
4. reproduces real CodeGenome executable unavailability;
5. fetches and installs exact Graphify release source;
6. verifies Graphify release and Apache-2.0 source-rights posture;
7. executes Graphify v1/v2 truth and currentness checks;
8. reproduces real Graphify executable unavailability;
9. emits exact-head provider qualification plus failure/fallback evidence;
10. validates schema, currentness, maturity, source-rights, fallback, and authority boundaries;
11. uploads provider-native, failure, and normalized artifacts.

Repository-wide doctrine validation remains independently required before merge.

## Relationship to configurable runtime and restart recovery

PRD-001 already requires deterministic configuration validation and states that fallback must not silently reduce maturity, scope/isolation, canonical/derived posture, qualification requirements, or governance requirements.

This implementation gives that requirement an executable provider-failure/fallback surface for the first capability family.

The same contract is now available to #282 restart recovery. Recovery does not need a second provider-resolution vocabulary. A provider missing after restart can remain explicitly unavailable; a configured fallback may be used only through the same current qualification and no-weaker checks.

## #300 completion boundary

PR #302 established the common adapter, applicability, raw evidence, source mutation/currentness, real-provider execution, and authority-none foundation.

PR #307 adds the previously missing provider-unavailable and no-weaker-fallback negative paths and synchronizes this runtime evidence document.

#300 may be closed only after the final PR #307 head has:

- focused qualification foundation CI green;
- exact CodeGenome/Graphify provider evidence CI green;
- repository-wide doctrine validation green;
- reconstructable exact-head evidence artifacts preserved.

Passing those gates completes this bounded harness. Broader CodeGenome qualification remains #293, EvolveAI qualification remains #292, configurable registry/runtime composition remains #280, and restart-safe multi-component acceptance remains #282.
