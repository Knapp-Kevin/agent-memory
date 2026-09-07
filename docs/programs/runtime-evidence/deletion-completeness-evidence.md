# P4.5 deletion-completeness evidence composition

Status: **Executable lifecycle composition**. This slice closes the evidence seam between the P4 canonical/derived-state residue model and P4.5 portable governance evidence. It does not change deletion semantics, accept an ADR, or raise a conformance level.

Parent implementation issue: #63.

## Why this composition exists

P4 already executes transitive purge and an independent residue sweep. P4.5a already carries `lifecycle_satisfaction` as a signed portable dimension. Those facts are necessary but, by themselves, do not prove that the portable lifecycle result was derived from the residue measurement rather than typed independently.

This composition makes that relationship executable:

```text
governed permanent deletion
        |
        v
P4 residue partition + independent sweep
        |
        | deterministic content-free measurement
        v
lifecycle = residual | satisfied
        |
        | signed by P4.5a
        v
portable deletion-completeness chain
```

The portable outcome is now a consequence of the P4 measurement.

## Public measurement

Schema: `../../../schemas/deletion-completeness-chain.schema.json`.

The public measurement contains counts, not projection identifiers:

```text
purged_count
declared_residual_controlled_count
declared_residual_uncontrollable_count
undeclared_residual_count
independently_observed_residual_count
total_residual_count
hard_gate_passed
lifecycle_satisfaction
```

The lifecycle rule is deliberately simple:

```text
total residual = 0  -> satisfied
total residual > 0  -> residual
```

The undeclared-residue gate remains separate:

```text
undeclared residual = 0  -> hard gate passed
undeclared residual > 0  -> hard gate failed
```

Therefore a deletion may be truthfully represented as `lifecycle = residual` while the undeclared-residue hard gate still passes, for example when a surviving projection is known, declared, and policy-retained. Conversely, undeclared residue is both residual lifecycle state and a hard-gate failure.

## Independent observation

The composition does not trust the purge to report its own success. The `independently_observed_residual_count` comes from `ProjectionGovernor.sweep(set())`, which deliberately supplies no declaration exemptions. It therefore re-derives all surviving content-bearing residue from the retained projection graph.

`measure_deletion_completeness()` rejects a partition that claims surviving declared or undeclared residue the independent sweep did not observe. A receipt cannot simply announce residue and have the measurement believe it.

## Executed scenarios

`../../../reference/tests/test_deletion_completeness_evidence.py` executes three paths.

### Declared residual

A transitive deletion is authorized and committed, but one content-bearing projection is retained by policy. The independent sweep observes the survivor.

Expected public result:

```text
independently_observed_residual_count = 1
total_residual_count                  = 1
undeclared_residual_count             = 0
hard_gate_passed                      = true
lifecycle_satisfaction                = residual
```

### Undeclared residual

A deliberately broken one-hop derived purge follows an authorized canonical deletion. A second-hop projection survives without being declared. The independent sweep catches it.

Expected public result:

```text
independently_observed_residual_count = 1
undeclared_residual_count             = 1
hard_gate_passed                      = false
lifecycle_satisfaction                = residual
```

This is the adversarial proof that the sweep can fail.

### Zero residue

The normal P4 transitive purge reaches the entire derivation closure and the independent sweep finds no surviving content-bearing projection.

Expected public result:

```text
independently_observed_residual_count = 0
total_residual_count                  = 0
undeclared_residual_count             = 0
hard_gate_passed                      = true
lifecycle_satisfaction                = satisfied
```

## Portable binding

Each scenario builds a P4.5a portable governance object whose:

```text
memory_action       = permanent_deletion
governance          = committed
after_state_ref     = sha256(public measurement)
lifecycle_result    = derived measurement lifecycle
canonical_receipt   = content-addressed canonical decision receipt
action_ref          = scenario-specific runtime action reference
```

The signed portable evidence remains verifiable against the canonical receipt and an independently observed runtime action.

The chain also records the exact Agent Memory commit SHA used to execute the scenario. CI passes the pull-request head SHA or push SHA explicitly rather than relying on a branch name.

## Privacy boundary

The public chain intentionally excludes:

- deleted memory content;
- canonical memory identifiers;
- projection identifiers;
- hidden reasoning;
- full canonical receipts.

Internal identifiers are required to execute a residue graph, but they are converted to counts and content-addressed references before the chain is serialized. The executable report fails if its known private fixture content or internal projection identifiers appear in the public JSON.

## Machine-readable report

`../../../reference/run_deletion_completeness.py` emits all three scenarios as JSON. CI runs:

```bash
python reference/run_deletion_completeness.py \
  --agent-memory-commit <exact-40-hex-commit> \
  --output deletion-completeness.json
```

and uploads that JSON as a workflow artifact.

The report is evidence, not a conformance declaration. It records the exact source commit, scenario measurements, signed P4.5a objects, and their content-addressed references.

## What this closes

This slice supplies executable evidence for the #63 lifecycle gate:

- P4 deletion completeness is exercised with residual and zero-residue outcomes;
- the independent sweep detects a surviving projection;
- the clean transitive purge demonstrates zero residual;
- signed portable evidence distinguishes the outcomes without deleted memory content.

It also covers both declared-residual and undeclared-residual negative cases, rather than treating every non-zero residue as the same governance condition.

## What remains separate

This composition does not prove:

- that a remote storage provider actually erased physical media;
- that an undeclared projection can always be discovered if it was never represented in the declaration/sweep surface;
- production key custody or trust discovery;
- upstream AgenTrust integration acceptance;
- AGT runtime-enforcement composition;
- ADR-020, ADR-021, or ADR-022 acceptance.

The declaration surface remains load-bearing. A sweep cannot find state the system has no observability path to inspect, which is why undeclared-state discovery outside the modeled projection universe remains an explicit limitation rather than a magical guarantee.
