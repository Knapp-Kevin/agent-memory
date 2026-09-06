# Portable runtime configuration evidence

Status: implementation evidence for #280

This slice establishes a machine-readable runtime composition contract for attaching Agent Memory to an existing stack without making the installer, serialization syntax, or component catalog authoritative.

## Earned claim

`runtime-configuration.schema.json@1.0.0` plus `reference/agentmem_ref/runtime_config.py` can deterministically validate and resolve a bounded Agent Memory runtime configuration that includes:

- an operator-managed agent runtime identity;
- an explicit canonical memory owner;
- a durable-governance profile/state reference;
- versioned component/capability declarations;
- adapter identity/runtime bindings;
- runtime source-rights posture;
- allowed/preferred provider routing;
- explicit fallback topology;
- independent qualification requirements;
- required derived-currentness projection identities;
- governance peer references;
- external secret references;
- qualification, receipt, and runtime-evidence store references.

The validated plan emits:

`authority_effect = none`

Configuration selects eligible implementation paths. It does not grant memory mutation, recall admission, structural, or external action authority.

## Primary installation posture

The reference fixture exercises:

`entry_mode = attach_existing_stack`

This reflects the expected dominant deployment sequence:

```text
existing runtime / governance / storage
  -> attach Agent Memory
  -> declare or discover components
  -> validate exact capabilities and versions
  -> bind independent qualification evidence where required
  -> resolve ambiguity / fallback topology
  -> declare currentness obligations
  -> start only from a validated posture
```

The fixture intentionally includes an operator-supplied canonical store and a DashClaw governance-peer reference. Agent Memory does not claim to have selected or installed either system.

## Qualified provider example

The first fixture composes the #300 code-graph qualification evidence:

```text
CodeGenome
  primary code_graph_traversal provider
  exact component + adapter + qualification applicability

Graphify
  explicit equivalent fallback
  independent current qualification
```

The checked-in `qualification-bindings.json` file is a normalized validation projection derived from the independently inspected #300 artifact.

The source qualification artifact remains the evidence authority. Editing the runtime configuration cannot make a component qualified.

## Fail-closed validation

The reference tests currently exercise refusal of:

- missing canonical-state owner;
- non-canonical owner posture;
- component-version drift with stale qualification;
- maturity shortfall;
- ambiguous provider selection;
- incompatible fallback posture;
- multiple equivalent fallbacks without an ordering/composition contract;
- runtime-disallowed source rights;
- non-current qualification;
- wrong primary qualification applicability digest;
- evidence-level maturity without independent qualification;
- required derived currentness without projection identity;
- literal credential material / invalid secret references.

The validator reuses ADR-033 `ComponentRegistry` resolution. It does not create an installer-specific provider-selection algorithm.

## Currentness and restart composition

A configuration route can declare a derived projection as correctness-required.

The reference fixture declares:

`code-graph`

This identity can be consumed by the #308 write-to-readable currentness contract and persisted/reconstructed by #282 restart-safe runtime work.

```text
configuration says projection is required
  != projection is current

projection observed current
  != runtime quiescent if another required obligation remains
```

## Secret boundary

Portable configuration records secret references only.

Current accepted reference schemes:

```text
env://
secret://
vault://
keyring://
```

Secret resolution is not implemented by this slice.

## Evidence command

```bash
python reference/run_runtime_configuration.py \
  --agent-memory-commit <exact-40-character-commit> \
  --output runtime-configuration-evidence.json
```

The `Runtime Configuration Contract` workflow runs:

1. targeted configuration tests;
2. the complete reference regression suite;
3. exact-head configuration resolution;
4. structural invariant validation;
5. evidence artifact upload.

## Non-claims and remaining #280 work

This slice does **not** complete #280.

It does not yet provide:

- interactive setup or setup wizard;
- package/component installation;
- automatic runtime/framework discovery;
- secret resolution;
- component marketplace/recommendation UX;
- a mandated JSON/YAML/TOML filename;
- general component removal/rebuild execution;
- complete multi-capability end-to-end memory operations through this config;
- restart-time migration between changed configurations;
- a service/CLI process that consumes this configuration in production form.

The next product-facing step can now build on a real contract rather than inventing configuration semantics inside a wizard.
