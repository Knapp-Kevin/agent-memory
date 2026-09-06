# Memory Unit Examples

## Purpose

These examples show how different memory types should be represented under the doctrine.

The point is not to freeze an implementation schema forever. The point is to make memory objects carry enough identity, provenance, evidence, lifecycle, uncertainty, and authority information that future systems cannot pretend a summary is the same thing as a governed memory. Tempting, but no.

These examples also demonstrate a critical boundary:

```text
estimator output != authority outcome != committed state transition
```

Implementations may use different field names. They should preserve the distinctions.

## Example: durable decision memory

```json
{
  "id": "uor:decision:project-memory-boundary",
  "type": "decision",
  "state": "crystallized",
  "content_ref": "repo://agent-memory/docs/adr/ADR-001-uor-is-identity-not-memory.md",
  "provenance": {
    "origin": "human-authored architecture decision",
    "observer": "agent-memory doctrine",
    "method": "ADR acceptance",
    "timestamp": "2026-07-06T00:00:00Z"
  },
  "evidence": [
    {
      "id": "evidence:adr-001",
      "kind": "architecture_decision_record",
      "ref": "docs/adr/ADR-001-uor-is-identity-not-memory.md",
      "confidence": 1,
      "confidence_kind": "direct_authoritative_record"
    }
  ],
  "saturation": {
    "sigma": 0.98,
    "score_kind": "lifecycle_routing_score",
    "calibrated": true,
    "estimator_id": "doctrine-saturation-example",
    "estimator_version": "v1",
    "calibration_version": "cal-example-v1",
    "calibration_scope": "doctrine decision memories",
    "uncertainty": {
      "representation": "categorical",
      "value": "low"
    },
    "threshold": 0.95,
    "durability_dimensions": ["approval", "cross_reference", "doctrine_dependency"]
  },
  "authority": {
    "pama_outcome": "allow_with_ledger",
    "risk_class": "high",
    "policy_refs": ["ADR-003", "ADR-004"],
    "policy_version": "doctrine-example-v1",
    "permitted_actions": ["crystallize"],
    "selection_mode": "deterministic"
  },
  "certification": {
    "status": "pass",
    "ref": "pull-request-review-or-merge-record",
    "scope": "doctrine"
  },
  "decision_receipt": {
    "requested_action": "crystallize",
    "selected_action": "crystallize",
    "before_state": "pending_verification",
    "after_state": "crystallized",
    "rollback_path": "dispute_or_correction_workflow",
    "ledger_ref": "ledger://example/decision-crystallization"
  }
}
```

### What this example demonstrates

- the saturation score is explicitly a lifecycle score, not a probability of truth
- estimator and calibration versions remain available
- PAMA outcome is separate from the score
- certification is separate from PAMA
- the committed transition has its own receipt

## Example: code artifact memory with uncertain semantic edge

```json
{
  "id": "uor:code:codegenome-overlay-edge",
  "type": "code_artifact",
  "state": "linked",
  "content_ref": "codegenome://graph/node/example",
  "provenance": {
    "origin": "CodeGenome graph extraction",
    "observer": "CodeGenome",
    "method": "tree-sitter plus semantic overlay",
    "timestamp": "2026-07-06T00:00:00Z"
  },
  "evidence": [
    {
      "id": "evidence:syntax-overlay",
      "kind": "syntax_overlay",
      "ref": "codegenome://overlay/syntax/example",
      "confidence": 1,
      "confidence_kind": "deterministic_parse_result"
    },
    {
      "id": "evidence:semantic-overlay",
      "kind": "semantic_overlay",
      "ref": "codegenome://overlay/semantic/example",
      "confidence": 0.8,
      "confidence_kind": "estimated_relation_confidence",
      "estimator_id": "semantic-edge-classifier",
      "estimator_version": "v3",
      "calibration_version": "edge-cal-2026-08",
      "uncertainty": {
        "representation": "interval",
        "lower": 0.68,
        "upper": 0.88
      }
    }
  ],
  "saturation": {
    "sigma": 0.71,
    "score_kind": "lifecycle_routing_score",
    "calibrated": true,
    "estimator_id": "code-memory-saturation",
    "estimator_version": "v2",
    "calibration_version": "code-cal-v2",
    "calibration_scope": "code relation memory",
    "uncertainty": {
      "representation": "categorical",
      "value": "medium"
    },
    "threshold": 0.95,
    "durability_dimensions": ["graph_reference", "impact_relevance", "observer_confidence"]
  },
  "authority": {
    "pama_outcome": "allow_with_ledger",
    "risk_class": "medium",
    "policy_refs": ["ADR-005"],
    "policy_version": "code-memory-policy-v1",
    "permitted_actions": ["retain_linked", "request_more_evidence"],
    "selection_mode": "planner_within_permitted_set"
  },
  "certification": {
    "status": "pending",
    "scope": "code-reality-graph"
  }
}
```

### What this example demonstrates

The exact syntax observation and the semantic relation do not share the same epistemic status. A graph can contain deterministic identity and probabilistic relations without pretending they are equivalent.

## Example: correction memory

```json
{
  "id": "uor:correction:stale-decision-update",
  "type": "correction",
  "state": "corrected",
  "content_ref": "ledger://corrections/stale-decision-update",
  "provenance": {
    "origin": "user correction",
    "observer": "governed memory runtime",
    "method": "dispute resolution workflow",
    "timestamp": "2026-07-06T00:00:00Z"
  },
  "evidence": [
    {
      "id": "evidence:user-correction",
      "kind": "human_correction",
      "ref": "ledger://corrections/stale-decision-update/source",
      "confidence": 1,
      "confidence_kind": "authoritative_user_correction"
    },
    {
      "id": "evidence:prior-state",
      "kind": "prior_memory_state",
      "ref": "ledger://memory/prior-version",
      "confidence": 1,
      "confidence_kind": "exact_ledger_reference"
    }
  ],
  "saturation": {
    "sigma": 0.97,
    "score_kind": "lifecycle_routing_score",
    "calibrated": true,
    "estimator_id": "correction-durability",
    "estimator_version": "v1",
    "calibration_version": "correction-cal-v1",
    "threshold": 0.95,
    "durability_dimensions": ["human_correction", "dispute_resolution", "audit_continuity"]
  },
  "authority": {
    "pama_outcome": "allow_with_ledger",
    "risk_class": "high",
    "policy_refs": ["ADR-004"],
    "policy_version": "correction-policy-v1",
    "permitted_actions": ["correct_preserve_history"],
    "selection_mode": "deterministic"
  },
  "certification": {
    "status": "pass",
    "ref": "ledger://corrections/stale-decision-update/certificate",
    "scope": "corrected-memory"
  },
  "decision_receipt": {
    "requested_action": "correct",
    "selected_action": "correct_preserve_history",
    "before_state": "disputed",
    "after_state": "corrected",
    "prior_state_ref": "ledger://memory/prior-version",
    "ledger_ref": "ledger://corrections/stale-decision-update/receipt"
  }
}
```

## Example: Shadow Genome failure memory

```json
{
  "id": "uor:failure:hallucination-permanence",
  "type": "failure",
  "state": "crystallized",
  "content_ref": "shadow-genome://failures/hallucination-permanence",
  "provenance": {
    "origin": "conformance failure analysis",
    "observer": "Shadow Genome",
    "method": "negative memory capture",
    "timestamp": "2026-07-06T00:00:00Z"
  },
  "evidence": [
    {
      "id": "evidence:failed-trap-class",
      "kind": "conformance_failure",
      "ref": "fixtures/confidently-wrong-memory.json",
      "confidence": 1,
      "confidence_kind": "observed_test_failure"
    }
  ],
  "saturation": {
    "sigma": 1,
    "score_kind": "lifecycle_routing_score",
    "calibrated": true,
    "estimator_id": "failure-durability",
    "estimator_version": "v1",
    "calibration_version": "failure-cal-v1",
    "threshold": 0.95,
    "durability_dimensions": ["safety_relevance", "failure_recurrence", "policy_dependency"]
  },
  "authority": {
    "pama_outcome": "allow_with_ledger",
    "risk_class": "critical",
    "policy_refs": ["ADR-002", "ADR-003", "ADR-004"],
    "policy_version": "negative-memory-policy-v1",
    "permitted_actions": ["crystallize_failure_memory"],
    "selection_mode": "deterministic"
  },
  "certification": {
    "status": "pass",
    "ref": "shadow-genome://certificates/hallucination-permanence",
    "scope": "negative-memory"
  }
}
```

## Example: uncertain promotion that abstains

```json
{
  "id": "uor:memory:uncertain-project-preference",
  "type": "preference",
  "state": "candidate",
  "content_ref": "memory://candidate/uncertain-project-preference",
  "provenance": {
    "origin": "inferred from repeated interactions",
    "observer": "preference-estimator",
    "method": "learned preference inference",
    "timestamp": "2026-08-10T00:00:00Z"
  },
  "estimate": {
    "claim": "user prefers behavior X in project Y",
    "confidence": 0.84,
    "estimator_id": "preference-inference",
    "estimator_version": "v5",
    "calibration_version": "pref-cal-v5",
    "calibration_scope": "project-scoped interaction preferences",
    "uncertainty": {
      "representation": "interval",
      "lower": 0.66,
      "upper": 0.91
    }
  },
  "authority": {
    "pama_outcome": "require_review",
    "risk_class": "high",
    "policy_version": "user-preference-policy-v2",
    "permitted_actions": ["store_ephemeral", "request_confirmation", "defer"],
    "prohibited_actions": ["crystallize", "expand_scope"],
    "selection_mode": "planner_within_permitted_set"
  },
  "decision_receipt": {
    "requested_action": "crystallize",
    "selected_action": "request_confirmation",
    "before_state": "candidate",
    "after_state": "pending_verification",
    "ledger_ref": "ledger://example/uncertain-preference-review"
  }
}
```

### What this example demonstrates

The estimate can be fairly confident and still lack authority to become durable user memory. The governance outcome narrows the available actions, and the planner may choose only inside that set.

## Example: high relevance blocked by scope

```json
{
  "query": "deployment credentials for service X",
  "retrieval_candidate": {
    "memory_id": "uor:secret:other-tenant-service-x",
    "semantic_relevance": 0.99,
    "retriever_id": "semantic-retriever",
    "retriever_version": "v7"
  },
  "governance": {
    "tenant_match": false,
    "sensitivity": "credential",
    "policy_version": "recall-policy-v4",
    "outcome": "block",
    "permitted_actions": []
  },
  "context_assembly": {
    "included": false
  }
}
```

High relevance is epistemic utility. It is not permission to cross scope.

## Example design rules

1. Distinguish exact evidence from estimated evidence.
2. Identify score semantics. A value between 0 and 1 is not automatically a probability.
3. Preserve estimator and calibration versions when estimates materially affect consequential decisions.
4. Preserve uncertainty rather than only a point estimate where the uncertainty affects policy.
5. Keep PAMA/policy outcome separate from estimator output.
6. Represent permitted and prohibited action sets where bounded stochastic choice matters.
7. Record policy version for consequential decisions.
8. Record the committed transition separately from the proposal.
9. Preserve rollback, dispute, or correction paths where applicable.
10. Do not require every implementation to copy this exact JSON shape.

## Rule

Examples are allowed to be implementation-flavored.

Doctrine docs are not.
