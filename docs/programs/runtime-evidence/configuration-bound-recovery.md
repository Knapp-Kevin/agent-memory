# Configuration-bound restart recovery

Status: implementation evidence for #282, composed with #280, #300, and #308

This slice binds the validated portable runtime configuration contract to restart-safe durable state without changing the already-earned `reference_file_checkpoint_v1` semantics.

## Why a second profile exists

The first restart profile proves that Agent Memory can reconstruct its reference substrate and governance envelope after restart.

The runtime configuration work adds another interpretation boundary:

```text
same durable bytes
+ different component routing / qualification / currentness requirements
= potentially different runtime meaning
```

Therefore configuration is not treated as startup-only convenience. A durable runtime must know which validated configuration interpretation produced and governs the state it is recovering.

The outer durability profile is:

`reference_config_bound_checkpoint_v1`

It composes, rather than replaces:

`reference_file_checkpoint_v1`

## Bound state

`configuration-binding.json` records:

- runtime-configuration digest;
- normalized resolved-plan digest and resolved plan;
- exact base checkpoint generation;
- base substrate digest;
- base governance digest;
- base interpretation digest;
- required #308 projection identities.

The outer binding is written after the inner checkpoint. If the inner checkpoint advances without a matching outer binding, recovery fails closed rather than pairing new durable memory with stale configuration interpretation.

## Configuration drift

Recovery requires both:

```text
configuration_digest == persisted configuration_digest
plan_digest == persisted plan_digest
```

A changed evidence-store reference, runtime profile, provider resolution, qualification record interpretation, or required projection set does not silently migrate existing durable state.

There is deliberately no automatic migration path in this slice.

## Provider failure after restart

A configured fallback is not activated from a boolean such as `provider_available = false`.

Fallback requires an explicit #300 `ProviderFailure` record matching the configured primary component and capability.

For the reference attach-to-existing-stack configuration:

```text
CodeGenome primary
  + explicit provider failure evidence
  + previously validated Graphify fallback binding
  -> Graphify fallback_active
```

Without failure evidence, CodeGenome remains the active configured primary.

A provider failure for a route with no configured fallback produces an explicit `unavailable` route activation and a degraded recovery posture. Durable-state recovery and operational readiness are therefore not collapsed.

Fallback/recovery evidence retains:

`authority_effect = none`

## Currentness composition

Persisted #308 visibility snapshots are checked against the recovered configuration's required projection identities.

A visibility obligation for a projection that is no longer required by the exact recovered configuration is refused rather than silently reinterpreted.

The reference fixture preserves the required:

`code-graph`

projection across restart.

## Evidence

Targeted tests:

```bash
python -m unittest discover -s reference/tests -t reference -p 'test_configured_restart.py'
```

Exact-head evidence:

```bash
python reference/run_config_bound_recovery.py \
  --agent-memory-commit <exact-40-character-commit> \
  --output config-bound-recovery.json
```

The workflow also runs the complete reference regression suite before preserving the evidence artifact.

## Non-claims

This slice does not provide:

- production distributed transaction semantics;
- automatic configuration migration;
- component package installation;
- interactive setup;
- live secret resolution;
- universal provider health monitoring;
- an HTTP/service runtime;
- a production CLI.

It establishes the runtime invariant those later product surfaces must preserve: durable Agent Memory state cannot be safely recovered under a different configuration interpretation merely because the files still parse.