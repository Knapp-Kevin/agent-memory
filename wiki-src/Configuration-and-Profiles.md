# Configuration and Profiles

Agent Memory does not have one global runtime configuration file because it is a reference architecture, evidence system, and set of optional implementation profiles rather than one monolithic product.

The useful question is therefore not "where is the `.env` file?" It is **which configuration surface controls the behavior you are using**.

## Current configuration surfaces

| You are configuring... | Start here |
|---|---|
| Canonical memory semantics | [`docs/`](https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/docs) and the [ADR index](https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/docs/adr) |
| Machine-readable records | [`schemas/`](https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/schemas) |
| Optional interoperability behavior | [`docs/profiles/`](https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/docs/profiles) |
| Reference dependencies and runners | [`reference/`](https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/reference) |
| Adversarial / doctrine fixtures | [`fixtures/`](https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/fixtures) |
| External source and license posture | [`sources/source-registry.json`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/sources/source-registry.json) |
| Wiki publication | [`wiki-src/`](https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/wiki-src) |
| CI and repository evidence | [`.github/workflows/`](https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/.github/workflows) |

There is currently no required repository-wide `.env`, YAML, or TOML runtime contract.

## Running the reference evidence environment

Install the checked-in reference dependencies and run the test suite:

```bash
python -m pip install -r reference/requirements.txt
python -m unittest discover -s reference/tests -t reference
```

A bounded conformance/evidence run may specify its trial count explicitly:

```bash
python reference/run_conformance.py --trials 500
```

That trial count configures the experiment. It does not change memory authority or lifecycle semantics.

See the canonical [Reference README](https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/reference) for current comparator commands and evidence boundaries.

## Optional real graph substrate

The reference evidence can additionally exercise a Graphiti/Kuzu temporal-graph path:

```bash
python -m pip install graphiti-core kuzu
python -m unittest discover -s reference/tests -t reference
python reference/run_conformance.py
```

This is optional. Installing a graph substrate does not make graph storage canonical Agent Memory state, and graph reachability does not become recall permission or mutation authority.

## Profiles

Profiles define bounded optional behavior such as interoperability, projection, evidence, or external-policy exchange.

A profile may configure an implementation, but it may not silently weaken a stricter canonical boundary:

```text
profile setting
!= lifecycle override
!= scope override
!= PAMA authority
```

Consequential consumers should reject unknown or incompatible profile versions rather than guessing that they are safe.

## Version binding

Keep independently meaningful versions separate when the evidence depends on them. Typical examples include:

- memory/schema version;
- PAMA decision version;
- policy version;
- profile/projection version;
- estimator/model/checkpoint version;
- external peer version;
- optional substrate/module version.

A version mismatch is a compatibility question, not a reason to fall back permissively.

## External dependencies and licensing

Agent Memory is licensed under Apache-2.0. External projects retain their own rights and licenses.

Before materially reusing an external dependency, fixture, asset, implementation, or documentation source, verify the exact source and reuse basis under the repository's [Source Rights Policy](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/SOURCE_RIGHTS_POLICY.md) and record it when required in the [source registry](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/sources/source-registry.json).

A linked or compared project is not relicensed merely because Agent Memory discusses it.

## Future modular memory profiles

Issue [#274](https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/274) owns the implementation program that will package completed cross-architecture research into optional graph, retrieval, transactional, learned/latent, and hybrid memory modules.

The common module configuration surface is expected to expose enough information to govern:

```text
module identity / type / version
capabilities
configuration profile
canonical-vs-derived posture
scope / isolation behavior
provenance / currentness bindings
correction / deletion / rebuild behavior
failure posture
migration / removal behavior
optional dependency / license metadata
```

No backend becomes canonical merely by being easy to install. Humanity has tried that strategy with databases before.

## Canonical reference

The full configuration contract and current commands live in [`docs/CONFIGURATION.md`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/CONFIGURATION.md).

Continue with the [Implementation Guide](Implementation-Guide), [Runtime Evidence](Runtime-Evidence), or [Conformance and Evidence](Conformance-and-Evidence) depending on what you are trying to build or verify.