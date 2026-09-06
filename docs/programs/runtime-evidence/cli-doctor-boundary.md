# Installed CLI and truthful doctor boundary

Status: implementation evidence for #282, consuming #280/#300/#308 contracts

This slice creates the first installed process boundary for the Agent Memory reference runtime.

It deliberately starts with diagnostics rather than a setup wizard. The goal is to make the existing configuration, qualification, currentness, and restart contracts usable from an installed command without inventing another configuration model.

## Installation boundary

The repository now contains Python package metadata and installs a console script:

```bash
python -m pip install .
agent-memory --help
```

The distribution name for this bounded reference slice is:

`agent-memory-reference`

The installed command is:

`agent-memory`

This does not claim a published PyPI release. It proves repository installation and console-script execution.

## Configuration validation

```bash
agent-memory config validate \
  --config path/to/runtime-config.json
```

For configurations that require independent qualification evidence:

```bash
agent-memory config validate \
  --config path/to/runtime-config.json \
  --qualifications path/to/qualification-bindings.json
```

The command consumes the same portable runtime schema, capability behavior contract, `ComponentRegistry`, source-rights checks, and qualification requirements used by the reference runtime.

It does not create a second installer-specific routing model.

Successful validation reports a configuration as startable under the bounded configuration contract. It does not claim the runtime is operationally healthy.

## Doctor

```bash
agent-memory doctor \
  --config path/to/runtime-config.json \
  --state-dir path/to/agent-memory-state
```

The diagnostic surface separates:

```text
configuration validity
durable-state presence
restart recovery
currentness / quiescence
live provider availability
operational readiness
```

These are intentionally not collapsed into one `healthy` Boolean.

### No durable state yet

A valid configuration with no initialized state reports:

```text
configuration = valid
durable_state = not_initialized
recovery = not_attempted
provider_availability = not_probed
operational_readiness = configuration_valid_state_not_initialized
```

This is a useful pre-start posture, not a recovery success.

### Exact bounded recovery

When `reference_config_bound_checkpoint_v1` state exists and matches the validated configuration/plan, doctor invokes the existing bounded recovery contract.

Successful recovery reports the exact durability profile, configuration/plan binding, checkpoint generation, and configured route activations.

It still reports:

`provider_availability = not_probed`

because successful file recovery does not prove a provider executable, network service, credential, or dependency is live now.

### Currentness

Persisted #308 visibility snapshots are reconstructed and summarized independently.

Possible aggregate statuses include:

```text
not_observed
pending
quiescent
degraded
not_proven
```

A pending required projection therefore remains visible as pending after restart instead of being hidden behind a generic process-up result.

### Recovery corruption

If the durable configuration/checkpoint binding fails the existing #282 recovery contract, doctor reports:

```text
recovery = failed_closed
configuration_startable = false
operational_readiness = blocked_by_recovery_failure
```

The CLI does not repair or migrate the state automatically.

## JSON output

Both commands support machine-readable output:

```bash
agent-memory config validate --config config.json --json
agent-memory doctor --config config.json --state-dir state --json
```

This allows the installed CLI to serve as a future automation/UX boundary without requiring a wizard to scrape human-formatted output.

## Exit behavior

The bounded command surface uses distinct refusal/error behavior:

- configuration/input refusal returns a nonzero refusal exit code;
- failed durable recovery or degraded currentness returns nonzero from doctor;
- pending currentness remains explicit in output instead of being converted into a fabricated failure or success;
- live provider availability remains unproven until an actual provider probe exists.

## Evidence

Targeted tests:

```bash
python -m unittest discover -s reference/tests -t reference -p 'test_cli_doctor.py'
```

Exact-head evidence:

```bash
python reference/run_cli_doctor.py \
  --agent-memory-commit <exact-40-character-commit> \
  --output cli-doctor-evidence.json
```

The `CLI Doctor Boundary` workflow additionally:

1. installs the distribution from the repository;
2. executes the installed `agent-memory` console script;
3. validates both the composed first-party and attach-to-existing-stack configurations;
4. runs targeted CLI/doctor tests;
5. runs the complete reference regression suite;
6. emits exact-head evidence;
7. refuses non-Boolean structural invariants;
8. preserves the diagnostic artifacts.

## Non-claims

This slice does not provide:

- a published PyPI package;
- setup wizard;
- automatic discovery of arbitrary runtimes/frameworks;
- component package installation;
- live secret resolution;
- universal provider health probes;
- HTTP/server API;
- production distributed durability;
- automatic configuration migration.

Those surfaces can now build on an installed command that already understands the canonical configuration/recovery contracts.

## Product direction

The intended sequence remains:

```text
existing runtime / governance / storage
  -> install Agent Memory
  -> validate/construct portable configuration
  -> qualify required components
  -> inspect durable/currentness posture
  -> start runtime
```

An eventual setup wizard should call these same validation/diagnostic APIs. It should not become the only place configuration semantics exist.