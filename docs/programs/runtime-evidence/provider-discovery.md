# Attach-mode discovery and provider availability probes

Issue: #318

## Purpose

Agent Memory is normally attached to an architecture that already exists. The discovery boundary therefore observes **explicit, bounded signals** about configured components rather than scanning the host and silently constructing configuration.

```text
existing runtime/configuration
  -> explicit probe manifest
  -> read-only observation
  -> availability evidence
  -> doctor reports availability separately
```

The following remain distinct:

```text
detected != configured
configured != qualified
qualified != available now
available now != healthy for every operation
available now != current/quiescent
probe success != authority
```

## Installed commands

```text
agent-memory discover \
  --config <runtime-config.json> \
  --probes <provider-probes.json>

agent-memory doctor \
  --config <runtime-config.json> \
  --probe \
  --probes <provider-probes.json>
```

`doctor` remains non-probing by default. Passing a probe manifest without `--probe` is refused rather than silently executing observations.

## Probe manifest

The manifest is separate from the portable runtime configuration in this first version. Each descriptor must bind to an already configured component or governance peer.

Supported bounded probe kinds:

- `executable`: resolve an explicit executable through the platform PATH/explicit executable lookup;
- `python_import`: resolve an explicit Python import specification;
- `filesystem_path`: test existence/type of an explicit filesystem path without reading its contents.

The schema is `schemas/provider-probes.schema.json` and is packaged with the installable distribution.

Probe targets cannot be `env://`, `secret://`, `vault://`, or `keyring://` references. Discovery does not resolve credentials and does not emit secret values.

## Evidence posture

Every probe result records:

- probe identity;
- configured subject identity;
- probe kind and explicit non-secret target;
- observation time;
- bounded lookup evidence;
- `available`, `unavailable`, `probe_failed`, or `unsupported` posture;
- whether the result satisfies a declared startability requirement;
- `authority_effect = none`.

A required unavailable probe blocks **declared provider startability**. It does not rewrite the runtime configuration or select a fallback.

An optional unavailable probe remains visible evidence but does not fabricate a required failure.

## Discovery is not installation

This implementation intentionally does not:

- enumerate all installed packages;
- inspect process tables, shell history, browser state, or home-directory contents;
- discover network services broadly;
- install or replace components;
- mutate the runtime configuration;
- resolve secrets;
- promote capability maturity;
- mark a provider healthy for every operation;
- change fallback selection;
- create PAMA, recall, structural, or execution authority.

The configuration remains operator-reviewable and declarative. Discovery can inform a future `init`/attach workflow, but observed state does not silently become durable configuration.

## Evidence

Exact-head CI runs:

```text
python -m unittest discover -s reference/tests -t reference -p 'test_provider_discovery.py'
python -m unittest discover -s reference/tests -t reference
python reference/run_provider_discovery.py \
  --agent-memory-commit <40-char-sha> \
  --output provider-discovery-evidence.json
```

The workflow also installs the repository distribution and invokes `agent-memory discover` and `agent-memory doctor --probe` through the installed console command, proving that packaged schema/resource resolution works outside source-tree imports.

## Current limitation

This slice establishes **availability signals**, not full service health. HTTP/network health probing is deliberately deferred until a bounded, source-rights-safe, credential-safe contract is justified. A successful executable or import probe means exactly what it says and nothing more.
