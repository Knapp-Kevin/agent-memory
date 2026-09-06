# Configuration and Extension Surfaces

Agent Memory now has a versioned **runtime configuration contract**, but it still does not require one privileged filename, serialization syntax, installer, or product shell.

That distinction matters. The semantic contract is canonical. JSON, a future YAML or TOML reader, a CLI, or an interactive setup wizard are presentation and transport layers over that contract.

Configuration selects and binds implementations. It does not redefine Agent Memory doctrine, prove a component qualified, create memory authority, or make a stale projection current.

## Current runtime configuration contract

The portable runtime configuration schema is:

`schemas/runtime-configuration.schema.json`

Current schema version:

`1.0.0`

Reference validator:

`reference/agentmem_ref/runtime/runtime_config.py`

Reference attach-to-existing-stack fixture:

`reference/fixtures/runtime-configuration/attached-existing-stack.json`

Executable evidence runner:

```bash
python reference/run_runtime_configuration.py \
  --agent-memory-commit <exact-40-character-commit> \
  --output runtime-configuration-evidence.json
```

The first checked-in serialization is JSON because the repository already uses JSON Schema for machine-readable contracts. This does **not** establish a required `agent-memory.json`, `agent-memory.yaml`, `agent-memory.toml`, or `.env` convention.

A future CLI or wizard must produce or edit an equivalent configuration and invoke the same validation semantics.

```text
serialization != semantics
wizard != configuration authority
installed != configured
configured != qualified
qualified != current
current != quiescent
```

## Primary installation assumption

The primary product assumption is that Agent Memory is usually attached to a stack that already exists.

Typical flow:

```text
existing agent runtime
+ existing governance / policy layer
+ existing storage / retrieval / tools
  -> declare or discover component identities
  -> create Agent Memory runtime configuration
  -> validate capabilities and source rights
  -> bind required qualification evidence
  -> resolve provider / fallback ambiguity
  -> declare currentness obligations
  -> start only from an explicit valid posture
```

`bootstrap_agent_memory_first` remains a supported entry-mode value for future Agent-Memory-first profiles, but it is not the primary assumption of this first implementation slice.

## What the runtime contract configures

The schema makes these boundaries explicit:

| Surface | Purpose |
|---|---|
| Runtime identity | Binds runtime, profile, version, and entry mode |
| Canonical-state owner | Declares which component/capability owns canonical retained state for the configured profile |
| Durable governance | Binds the governance durability profile and state reference |
| Components | Declares exact component/version/capability posture using the ADR-033 vocabulary |
| Adapters | Binds adapter identity, version, runtime reference, and secret references |
| Source rights | Records license/source reference and runtime/comparator/disallowed posture |
| Routes | Declares capability/version/maturity requirements plus allowed/preferred providers |
| Fallback | Declares explicit fallback candidates; no registration-order fallback is implied |
| Qualification | Binds independently supplied qualification profile/applicability requirements |
| Currentness | Declares which derived projections are correctness-required for the active profile |
| Governance peers | References existing governance/policy peers without making them Agent Memory doctrine dependencies |
| Evidence stores | References qualification, receipt, and runtime-evidence locations |

An external product's native configuration format is never automatically an Agent Memory configuration format.

## Configuration is not qualification

Component declarations and runtime configuration are operator/runtime intent. Qualification is independent evidence.

The validator therefore consumes qualification bindings separately from the configuration file for routes that require evidence-level maturity.

The reference fixture uses normalized bindings derived from the independently validated #300 CodeGenome/Graphify qualification artifact. That checked-in fixture is a validation projection, not the source evidence authority.

```text
component declared
  != component qualified

component selected by configuration
  != qualification current

qualification current
  != mutation authority
```

For a route requiring `evidence_proven` or `reference_qualified`, the reference validator refuses startup if independent qualification is not required and supplied.

The validator also binds the configured primary qualification to exact equivalents of:

```text
component id/version
capability id/version
adapter id/version
qualification profile id/version
applicability digest
qualification currentness
earned maturity
source-rights use posture
```

A changed component version does not silently inherit qualification.

## Deterministic provider selection

Runtime routing reuses the existing `ComponentRegistry` and ADR-033 capability declarations. There is no second installer-specific routing model.

A route may specify:

```text
capability id/version
minimum maturity
allowed components
preferred component
required state posture
required scope posture
explicit fallback components
qualification requirement
currentness requirement
```

If more than one provider remains eligible and no explicit preference resolves the ambiguity, validation fails.

If a configured fallback is weaker or incompatible in material posture, validation fails.

The first configuration contract also rejects multiple equivalent fallback candidates because it does not yet define an ordering or composition rule. It will not invent first-match behavior from array order.

Execution-time provider failure remains governed by the #300 fallback contract. Pre-start configuration validation does not replace runtime failure evidence.

## Canonical state and durable governance

The active profile must explicitly name its canonical-state owner component and capability.

The referenced capability must:

- exist at the configured version;
- be enabled;
- declare `state_posture = canonical`;
- be permitted for runtime use under its source-rights posture.

Durable governance state is configured separately from the canonical memory owner because these are distinct obligations.

The current reference durability profile from #282 is:

`reference_file_checkpoint_v1`

That profile is bounded reference evidence, not a universal storage recommendation.

```text
canonical memory storage
!= governance metadata durability
!= provider qualification
!= read-path currentness
```

## Currentness obligations

The runtime configuration can declare a route as correctness-required for current visibility.

For derived state, a required currentness route must name a projection identity. That projection identity can be consumed by the #308 write-to-readable visibility contract and later by #282 restart recovery.

The reference attach fixture declares:

`code-graph`

as a required derived projection.

A successful component invocation does not by itself satisfy that currentness obligation.

## Secret handling

Portable runtime configuration accepts **secret references**, not literal credentials.

The first reference validator accepts these schemes:

```text
env://
secret://
vault://
keyring://
```

Examples:

```text
env://EXISTING_MEMORY_DSN
env://DASHCLAW_TOKEN
vault://agent-memory/production/provider
```

Secret resolution is deliberately outside this slice. A future CLI or runtime integration may resolve these references through an appropriate credential provider, but the portable configuration must not become a credential dump.

The validator additionally rejects common literal-secret field names even if a future schema edit accidentally becomes more permissive.

## Source rights are runtime configuration

Every configured component carries an explicit runtime source-rights posture:

```text
runtime_allowed
comparator_only
disallowed
```

A component selected for runtime use must be `runtime_allowed`.

The configuration must also preserve its license/source reference. Agent Memory's Apache-2.0 license covers this repository's own licensed distribution. It does not relicense a component merely because the runtime can call it.

Before adding a material external dependency, copied asset, comparator, source-derived fixture, or adapted implementation:

1. identify the exact source;
2. verify the applicable license or permission basis;
3. choose citation, independent synthesis, licensed reuse, author-originated reuse, or explicit permission deliberately;
4. add or update `sources/source-registry.json` when required by [`SOURCE_RIGHTS_POLICY.md`](SOURCE_RIGHTS_POLICY.md);
5. preserve any required attribution, NOTICE, modification notice, trademark, or redistribution obligation.

## Existing repository configuration surfaces

The runtime configuration contract does not replace narrower repository surfaces that have different owners.

| Surface | Canonical location | What it configures |
|---|---|---|
| Runtime composition | `schemas/runtime-configuration.schema.json` | Component topology, routing, qualification requirements, currentness and peer references |
| Doctrine and lifecycle semantics | `docs/`, `docs/adr/` | Meaning, ownership, maturity, lifecycle and governance boundaries |
| Other machine-readable contracts | `schemas/` | Valid record and evidence shapes |
| Interoperability / implementation profiles | `docs/profiles/` and matching schemas | Optional cross-system behavior and evidence boundaries |
| Reference validation dependencies | `reference/requirements.txt` | Pinned dependencies used by the main reference test environment |
| Reference runner options | `reference/run_*.py` | Bounded evidence-runner inputs |
| Doctrine / adversarial scenarios | `fixtures/` | Structural and negative-path expectations |
| Source-rights records | `sources/source-registry.json` | External source, license, provenance, and reuse posture |
| Wiki publication | `wiki-src/` + `.github/workflows/publish-wiki.yml` | Reader-facing documentation source and publication |
| CI behavior | `.github/workflows/` | Repository evidence and validation execution |

## Reference environment

The main executable evidence environment is installed from the checked-in dependency manifest:

```bash
python -m pip install -r reference/requirements.txt
python -m unittest discover -s reference/tests -t reference
```

The reference environment is intentionally broader than the low-cost documentation/fixture validators because it exercises cryptographic, interoperability, configuration, and runtime evidence paths.

See [`../reference/README.md`](../reference/README.md) for the current executable evidence boundary and comparator commands.

## Profiles are configuration with semantics

Files under `docs/profiles/` define optional implementation or interoperability contracts. A profile may describe governance context projection, portable evidence, external policy composition, runtime correlation, or another bounded behavior.

Profile configuration remains subordinate to canonical doctrine:

```text
profile setting
-> selects or parameterizes allowed implementation behavior

profile setting
!= permission to weaken a stricter lifecycle / scope / PAMA boundary
```

Unknown or incompatible consequential profile versions should fail explicitly rather than being coerced into a permissive default.

## Schema and policy version binding

When a runtime or evidence record depends on a schema, policy, projection, estimator, external consumer, module, adapter, or qualification configuration, bind the relevant version or stable identity whenever the corresponding contract requires it.

Do not collapse independent version dimensions into one generic `version` field when their drift has different consequences.

Examples include:

```text
runtime configuration schema version
runtime profile version
component/capability version
adapter version
qualification profile version
qualification applicability digest
memory schema version
PAMA decision schema version
policy version
projection/currentness identity
external peer version
estimator/model version
```

Version drift is evidence to evaluate, not permission to guess compatibility.

## Future installer and setup UX

A future installation experience should be a client of this contract.

Likely command surfaces may include equivalents of:

```text
agent-memory init
agent-memory config validate
agent-memory discover
agent-memory component list
agent-memory component add
agent-memory qualify
agent-memory doctor
agent-memory serve
```

These commands are not implemented by this configuration slice and are not yet public CLI commitments.

The intended UX boundary is nevertheless explicit:

- inspect or ask about the user's existing runtime/governance/storage stack;
- construct the portable configuration;
- validate deterministic component routing and source rights;
- resolve or surface qualification requirements;
- refuse ambiguity instead of guessing;
- keep credentials external through secret references;
- report currentness/recovery posture separately from installation success.

Suggested components may eventually be offered during setup, but a recommendation should expose exact qualified version, maturity, supported capability, limitations, source-rights posture, and evidence basis. Popularity is not qualification.

## Configuration review checklist

A configuration or extension change is not complete merely because it starts successfully. Review whether it:

- preserves canonical doctrine ownership;
- binds consequential versions and identities;
- names canonical-state ownership explicitly;
- separates component declaration from qualification evidence;
- fails explicitly when required configuration or qualification is unknown or stale;
- rejects ambiguous provider selection;
- prevents fallback from silently weakening material posture;
- keeps optional dependencies optional;
- preserves scope and isolation boundaries;
- records required derived currentness obligations;
- keeps secrets out of portable configuration values;
- does not turn estimator/backend capability into authority;
- records source-rights and license posture;
- updates README, canonical docs, Wiki, and visuals when the public architecture actually changes;
- produces evidence appropriate to the claim being made.

Configuration is an implementation surface. Agent Memory semantics remain governed by canonical doctrine, schemas, profiles, evidence, and accepted architecture decisions.

## Seal anchors

Every `SESSION SEAL` in `docs/META_LEDGER.md` records the `git write-tree` oid of the staged index at seal time. Those trees are anchored as parentless commits under `refs/seals/entry-<N>` so they are reachable, pushed, and safe from `git gc`. **A default `git clone` does not fetch this namespace.** To verify seals in a checkout:

```
git fetch origin 'refs/seals/*:refs/seals/*'
python scripts/verify_seals.py
```

`verify_seals.py` fails -- rather than passing vacuously -- if the ledger records seals and the namespace is empty. New seals are anchored at substantiate with `python scripts/anchor_seal.py <entry>` and pushed with `git push origin 'refs/seals/*:refs/seals/*'`.
