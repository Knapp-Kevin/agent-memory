"""Deterministic current-context recall admission policy for issue #200.

This module is deliberately content-agnostic. It receives a candidate reference,
current recall context, current policy version, and bounded evidence/risk refs.
It can tighten recall admission for the current request, but it cannot mutate
memory, turn relevance or estimator output into authority, or create standing
permission from a prior admission.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import rfc8785

from . import receipts

PROFILE_VERSION = "0.1.0"
ADMITTING_OUTCOMES = {"admit", "admit_with_warning"}
OUTCOMES = ADMITTING_OUTCOMES | {"require_verification", "require_review", "quarantine", "block"}


def _sha256_ref(value: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def context_projection(context: object) -> dict[str, Any]:
    """Project only bounded identity/purpose fields from RecallContext-like input."""
    domains = tuple(getattr(context, "target_domain_refs", ()) or ())
    if not all(isinstance(item, str) and item for item in domains):
        raise ValueError("target_domain_refs must contain non-empty strings")
    return {
        "target_domain_refs": list(dict.fromkeys(domains)),
        "principal_ref": str(getattr(context, "principal_ref", "") or ""),
        "project_ref": str(getattr(context, "project_ref", "") or ""),
        "task_ref": str(getattr(context, "task_ref", "") or ""),
        "purpose": str(getattr(context, "purpose", "") or ""),
        "destination_ref": str(getattr(context, "destination_ref", "") or ""),
    }


def build_decision(
    *,
    candidate_ref: str,
    context: object,
    policy_ref: str,
    policy_version: str,
    policy_status: str,
    outcome: str,
    reason_code: str,
    evidence_refs: tuple[str, ...] | list[str] = (),
    evaluated_at: str,
    risk_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not candidate_ref:
        raise ValueError("candidate_ref is required")
    if not policy_ref or not policy_version:
        raise ValueError("policy_ref and policy_version are required")
    if policy_status not in {"evaluated", "unavailable", "error", "invalid"}:
        raise ValueError(f"invalid policy_status {policy_status!r}")
    if outcome not in OUTCOMES:
        raise ValueError(f"unsupported contextual recall outcome {outcome!r}")
    if not reason_code:
        raise ValueError("reason_code is required")
    refs = list(dict.fromkeys(evidence_refs))
    if not all(isinstance(item, str) and item for item in refs):
        raise ValueError("evidence_refs must contain non-empty strings")

    identity = {
        "candidate_ref": candidate_ref,
        "policy_ref": policy_ref,
        "policy_version": policy_version,
        "policy_status": policy_status,
        "context": context_projection(context),
        "outcome": outcome,
        "reason_code": reason_code,
        "evidence_refs": refs,
        "risk_evidence": risk_evidence,
    }
    document: dict[str, Any] = {
        "schema_version": "1.0.0",
        "profile_version": PROFILE_VERSION,
        "decision_id": f"contextual-recall:{_sha256_ref(identity)}",
        "candidate_ref": candidate_ref,
        "policy": {
            "policy_ref": policy_ref,
            "policy_version": policy_version,
            "status": policy_status,
            "selection_mode": "deterministic",
        },
        "context": identity["context"],
        "outcome": outcome,
        "reason_code": reason_code,
        "evidence_refs": refs,
        "evaluated_at": evaluated_at,
        "interpretation": {
            "authority_effect": "current_recall_only",
            "prior_admission_authority": "none",
            "memory_mutation": "not_performed",
            "relevance_authority": "none",
            "risk_signal_authority": "none",
        },
    }
    if risk_evidence is not None:
        document["risk_evidence"] = dict(risk_evidence)
    receipts.validate("contextual-recall-admission.schema.json", document)
    return document


@dataclass(frozen=True)
class ContextualRule:
    rule_id: str
    outcome: str
    reason_code: str
    candidate_ref: str = ""
    purpose: str = ""
    destination_ref: str = ""
    principal_ref: str = ""
    project_ref: str = ""
    task_ref: str = ""
    evidence_refs: tuple[str, ...] = ()
    risk_evidence: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.rule_id:
            raise ValueError("rule_id is required")
        if self.outcome not in OUTCOMES:
            raise ValueError(f"unsupported contextual recall outcome {self.outcome!r}")
        if not self.reason_code:
            raise ValueError("reason_code is required")

    def matches(self, candidate_ref: str, context: object) -> bool:
        expected = {
            "candidate_ref": self.candidate_ref,
            "purpose": self.purpose,
            "destination_ref": self.destination_ref,
            "principal_ref": self.principal_ref,
            "project_ref": self.project_ref,
            "task_ref": self.task_ref,
        }
        observed = {
            "candidate_ref": candidate_ref,
            "purpose": str(getattr(context, "purpose", "") or ""),
            "destination_ref": str(getattr(context, "destination_ref", "") or ""),
            "principal_ref": str(getattr(context, "principal_ref", "") or ""),
            "project_ref": str(getattr(context, "project_ref", "") or ""),
            "task_ref": str(getattr(context, "task_ref", "") or ""),
        }
        return all(not value or observed[field] == value for field, value in expected.items())


class DeterministicContextualRecallPolicy:
    """Simple deterministic rule policy used by the reference adapter/harness.

    Rules may be informed by learned/probabilistic risk evidence, but the rule's
    explicit outcome is the governed consequence. The signal itself is never
    interpreted as permission.
    """

    def __init__(
        self,
        *,
        policy_ref: str,
        policy_version: str,
        rules: tuple[ContextualRule, ...] = (),
        default_outcome: str = "admit",
        default_reason_code: str = "no_contextual_restriction",
    ) -> None:
        if not policy_ref or not policy_version:
            raise ValueError("policy_ref and policy_version are required")
        if default_outcome not in OUTCOMES:
            raise ValueError(f"unsupported contextual recall outcome {default_outcome!r}")
        self.policy_ref = policy_ref
        self.policy_version = policy_version
        self.rules = tuple(rules)
        self.default_outcome = default_outcome
        self.default_reason_code = default_reason_code
        self.evaluation_count = 0

    def evaluate(self, candidate_ref: str, context: object, *, evaluated_at: str) -> dict[str, Any]:
        self.evaluation_count += 1
        for rule in self.rules:
            if rule.matches(candidate_ref, context):
                return build_decision(
                    candidate_ref=candidate_ref,
                    context=context,
                    policy_ref=self.policy_ref,
                    policy_version=self.policy_version,
                    policy_status="evaluated",
                    outcome=rule.outcome,
                    reason_code=rule.reason_code,
                    evidence_refs=rule.evidence_refs,
                    evaluated_at=evaluated_at,
                    risk_evidence=rule.risk_evidence,
                )
        return build_decision(
            candidate_ref=candidate_ref,
            context=context,
            policy_ref=self.policy_ref,
            policy_version=self.policy_version,
            policy_status="evaluated",
            outcome=self.default_outcome,
            reason_code=self.default_reason_code,
            evaluated_at=evaluated_at,
        )


def fail_closed_decision(
    *,
    candidate_ref: str,
    context: object,
    policy_ref: str,
    policy_version: str,
    status: str,
    reason_code: str,
    evaluated_at: str,
) -> dict[str, Any]:
    if status not in {"unavailable", "error", "invalid"}:
        raise ValueError("fail-closed status must be unavailable, error, or invalid")
    return build_decision(
        candidate_ref=candidate_ref,
        context=context,
        policy_ref=policy_ref,
        policy_version=policy_version,
        policy_status=status,
        outcome="block",
        reason_code=reason_code,
        evidence_refs=(),
        evaluated_at=evaluated_at,
    )
