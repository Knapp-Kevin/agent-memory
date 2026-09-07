# Predictive and Counterfactual Memory Reference

Status: **bounded runtime reference for issue #348**

Capability: `predictive_counterfactual_memory@1.0`

Component: `agent-memory-predictive-reference@0.1.0`

## Purpose

Capability Contract v3 introduced an explicit retained-memory capability for predictions, simulations, expected outcomes, counterfactual trajectories, and later outcome comparison. This reference makes that boundary executable without embedding a simulation engine or allowing predicted state to become observed history by storage accident.

The retained paths are deliberately separate:

```text
prediction revision
  -> stable prediction identity
  -> explicitly predictive kind
  -> Cognitive Mesh
  -> PAMA
  -> governed predictive memory

observed outcome evidence
  -> separate comparison artifact
  -> exact prediction revision reference
  -> descriptive disposition
  -> Cognitive Mesh
  -> PAMA
  -> governed comparison memory
```

The second path does not overwrite the first.

## Predictive state

Each prediction has one stable `prediction_ref` and append-only `revision_ref` lineage. A revision records:

- predictive kind: `forecast`, `simulation`, or `counterfactual`;
- expected outcome;
- confidence when supplied;
- target window / horizon description;
- basis evidence refs;
- assumptions;
- prior revision ref and revision reason;
- governed scope/isolation/project/task/purpose;
- source component and optional estimator identity/version.

Predictive revisions use PAMA `tentative` strength. Retention therefore does not imply observation, truth, or authority. A later revision must extend the exact current revision, keep the same predictive kind, and retain the same governed scope.

Initial retention uses the existing `promotion` operation. Later revision uses the existing `correction` operation, preserving current review requirements. Confidence is estimator evidence only and cannot discharge an authority requirement.

## Outcome comparison

`PredictionOutcomeComparison` is a distinct derived artifact. It records:

- a stable comparison ref;
- exact `prediction_ref` and `prediction_revision_ref`;
- observed outcome summary;
- observed evidence refs;
- observation time;
- comparison disposition: `matched`, `contradicted`, `partial`, or `unresolved`;
- optional comparison evidence and estimator metadata.

The comparison retains a reference to observed evidence. It is not itself promoted to `semantic_fact_memory` or `episodic_event_memory` by this module.

The comparison disposition is provider/estimator output. `matched` does not authorize action, `contradicted` does not autonomously block action, and a confidence of `1.0` does not alter PAMA outcome.

## Counterfactual boundary

Counterfactual history is intentionally sticky:

```text
counterfactual prediction
  + later actual outcome
  + comparison
  != observed counterfactual history
```

The actual outcome can be compared with the counterfactual, but `prediction_kind` remains `counterfactual`. The original expected outcome remains historically attributable as the modelled branch that was considered, not as an event that happened.

## Capability maturity and operational honesty

The reference component declares:

```text
profile_version: component-capability-v3
maturity: runtime_wired
authority_effect: none
```

Its operational contract is intentionally process-local:

```text
write_atomicity: process_local
concurrency_control: process_local
idempotency: process_local
restart_recovery: process_local_only
reconciliation: process_local_only
```

This slice proves predictive semantics, governed retention/revision, and the observed-outcome comparison boundary. It does not prove restart reconstruction, cross-process reconciliation, or production world-model execution.

## Non-claims

This implementation does not:

- execute forecasts, simulations, or counterfactual models;
- certify a prediction as fact;
- treat an observed outcome summary as canonical observed history;
- promote comparison disposition to authority;
- treat confidence `1.0` as permission;
- provide cross-process restart reconstruction;
- claim durable idempotency or reconciliation;
- add an external world-model/provider SDK;
- create a new PAMA operation or authority class.

External predictive providers can later be qualified against Capability Contract v3 without changing these canonical semantic boundaries.
