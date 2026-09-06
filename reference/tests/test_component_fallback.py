from __future__ import annotations

import unittest

from agentmem_ref.capabilities import ResolvedCapability
from agentmem_ref.component_fallback import (
    FallbackError,
    ProviderFailure,
    QualifiedCapability,
    evaluate_explicit_fallback,
)
from agentmem_ref.qualification import (
    AdapterResult,
    QualificationRuntime,
    QualificationSubject,
    qualification_from_adapter_results,
)


CAPABILITY = "code_graph_traversal"
PROFILE = "code-graph-traversal-currentness-failure"


def resolved(
    component_id: str,
    *,
    maturity: str = "evidence_proven",
    state_posture: str = "derived",
    scope_posture: str = "inherits_agent_memory_scope",
    failure_posture: str = "explicit_unavailable",
    authority_effect: str = "none",
) -> ResolvedCapability:
    return ResolvedCapability(
        component_id=component_id,
        component_version="1.0.0",
        profile_version="component-profile-v1",
        capability_id=CAPABILITY,
        capability_version="1.0",
        maturity=maturity,
        state_posture=state_posture,
        scope_posture=scope_posture,
        failure_posture=failure_posture,
        authority_effect=authority_effect,
        evidence_refs=(f"evidence:{component_id}",),
    )


def qualification(
    component_id: str,
    *,
    earned: str = "evidence_proven",
    use_posture: str = "runtime_allowed",
    profile: str = PROFILE,
    profile_version: str = "1.0.0",
    current: bool = True,
):
    subject = QualificationSubject(
        component_id=component_id,
        component_version="1.0.0",
        implementation_ref=f"fixture/{component_id}@1.0.0",
        capability_id=CAPABILITY,
        capability_version="1.0",
        adapter_id=f"{component_id}-adapter",
        adapter_version="1.0.0",
        qualification_profile_id=profile,
        qualification_profile_version=profile_version,
    )
    runtime = QualificationRuntime(
        configuration_digest="sha256:" + "a" * 64,
        fixture_id="fallback-fixture",
        fixture_digest="sha256:" + "b" * 64,
        runtime_refs=("python:3.12",),
    )
    result = AdapterResult(
        subject=subject,
        operation="query",
        runtime_identity=f"runtime:{component_id}",
        input_refs=("fixture:query",),
        raw_provider_refs=(f"raw:{component_id}",),
        normalized_refs=(f"normalized:{component_id}",),
        currentness="current",
        failure_result="none",
        trace_ref=f"trace:{component_id}",
    )
    record = qualification_from_adapter_results(
        subject=subject,
        runtime=runtime,
        license_id="MIT",
        license_ref=f"license:{component_id}",
        use_posture=use_posture,
        results=(result,),
        checks=(("query", True, f"normalized:{component_id}"),),
        artifact_digests=("sha256:" + "c" * 64,),
        maturity_before="runtime_wired",
        profile_maturity_ceiling="evidence_proven",
        earned_maturity=earned,
    )
    if current:
        return record
    return type(record)(
        subject=record.subject,
        runtime=record.runtime,
        license_id=record.license_id,
        license_ref=record.license_ref,
        use_posture=record.use_posture,
        operations=record.operations,
        raw_provider_refs=record.raw_provider_refs,
        normalized_refs=record.normalized_refs,
        checks=record.checks,
        artifact_digests=record.artifact_digests,
        maturity_before=record.maturity_before,
        profile_maturity_ceiling=record.profile_maturity_ceiling,
        earned_maturity=record.earned_maturity,
        adapter_results=record.adapter_results,
        limitations=record.limitations,
        qualification_current=False,
    )


def qualified(component_id: str, **kwargs) -> QualifiedCapability:
    resolved_kwargs = {
        key: kwargs[key]
        for key in ("maturity", "state_posture", "scope_posture", "failure_posture", "authority_effect")
        if key in kwargs
    }
    qualification_kwargs = {
        key: kwargs[key]
        for key in ("earned", "use_posture", "profile", "profile_version", "current")
        if key in kwargs
    }
    return QualifiedCapability(
        resolved(component_id, **resolved_kwargs),
        qualification(component_id, **qualification_kwargs),
    )


class ComponentFallbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.primary = qualified("primary")
        self.failure = ProviderFailure(
            component_id="primary",
            capability_id=CAPABILITY,
            failure_result="provider_unavailable",
            evidence_ref="raw:primary-unavailable",
            trace_ref="trace:primary-unavailable",
        )

    def test_no_configured_fallback_remains_explicitly_unavailable(self) -> None:
        decision = evaluate_explicit_fallback(
            primary=self.primary,
            failure=self.failure,
            candidates=(qualified("equivalent"),),
            allowed_components=(),
        )
        self.assertEqual(decision.status, "unavailable")
        self.assertEqual(decision.reason, "fallback_not_configured")
        self.assertEqual(decision.authority_effect, "none")

    def test_explicit_equivalent_fallback_is_selected(self) -> None:
        decision = evaluate_explicit_fallback(
            primary=self.primary,
            failure=self.failure,
            candidates=(qualified("equivalent"),),
            allowed_components=("equivalent",),
        )
        self.assertEqual(decision.status, "fallback_selected")
        self.assertEqual(decision.selected_component_id, "equivalent")
        self.assertEqual(decision.reason, "explicit_equivalent_fallback")

    def test_weaker_maturity_is_not_fallback(self) -> None:
        decision = evaluate_explicit_fallback(
            primary=self.primary,
            failure=self.failure,
            candidates=(qualified("weaker", maturity="runtime_wired", earned="evidence_proven"),),
            allowed_components=("weaker",),
        )
        self.assertEqual(decision.status, "unavailable")
        self.assertIn("weaker_maturity", decision.rejected_candidates[0][1])

    def test_scope_posture_cannot_weaken_or_change(self) -> None:
        decision = evaluate_explicit_fallback(
            primary=self.primary,
            failure=self.failure,
            candidates=(qualified("scope-change", scope_posture="external_scope_bridge"),),
            allowed_components=("scope-change",),
        )
        self.assertEqual(decision.status, "unavailable")
        self.assertIn("scope_posture_mismatch", decision.rejected_candidates[0][1])

    def test_state_posture_cannot_change(self) -> None:
        decision = evaluate_explicit_fallback(
            primary=self.primary,
            failure=self.failure,
            candidates=(qualified("state-change", state_posture="external"),),
            allowed_components=("state-change",),
        )
        self.assertEqual(decision.status, "unavailable")
        self.assertIn("state_posture_mismatch", decision.rejected_candidates[0][1])

    def test_failure_posture_cannot_change_silently(self) -> None:
        decision = evaluate_explicit_fallback(
            primary=self.primary,
            failure=self.failure,
            candidates=(qualified("failure-change", failure_posture="fail_open_candidate_only"),),
            allowed_components=("failure-change",),
        )
        self.assertEqual(decision.status, "unavailable")
        self.assertIn("failure_posture_mismatch", decision.rejected_candidates[0][1])

    def test_comparator_only_source_rights_cannot_be_runtime_fallback(self) -> None:
        decision = evaluate_explicit_fallback(
            primary=self.primary,
            failure=self.failure,
            candidates=(qualified("comparator", use_posture="comparator_only"),),
            allowed_components=("comparator",),
        )
        self.assertEqual(decision.status, "unavailable")
        self.assertIn("source_rights_not_runtime_allowed", decision.rejected_candidates[0][1])

    def test_stale_qualification_cannot_be_runtime_fallback(self) -> None:
        decision = evaluate_explicit_fallback(
            primary=self.primary,
            failure=self.failure,
            candidates=(qualified("stale", current=False),),
            allowed_components=("stale",),
        )
        self.assertEqual(decision.status, "unavailable")
        self.assertIn("qualification_not_current", decision.rejected_candidates[0][1])

    def test_different_qualification_profile_cannot_inherit_currentness_semantics(self) -> None:
        decision = evaluate_explicit_fallback(
            primary=self.primary,
            failure=self.failure,
            candidates=(qualified("different-profile", profile="different-profile"),),
            allowed_components=("different-profile",),
        )
        self.assertEqual(decision.status, "unavailable")
        self.assertIn("qualification_profile_mismatch", decision.rejected_candidates[0][1])

    def test_multiple_equivalent_fallbacks_are_ambiguous_not_first_match(self) -> None:
        decision = evaluate_explicit_fallback(
            primary=self.primary,
            failure=self.failure,
            candidates=(qualified("a"), qualified("b")),
            allowed_components=("a", "b"),
        )
        self.assertEqual(decision.status, "unavailable")
        self.assertEqual(decision.reason, "ambiguous_equivalent_fallbacks")
        self.assertIsNone(decision.to_dict()["selected_component_id"])

    def test_failure_must_belong_to_selected_primary(self) -> None:
        wrong = ProviderFailure(
            component_id="someone-else",
            capability_id=CAPABILITY,
            failure_result="provider_unavailable",
            evidence_ref="raw:failure",
            trace_ref="trace:failure",
        )
        with self.assertRaises(FallbackError):
            evaluate_explicit_fallback(
                primary=self.primary,
                failure=wrong,
                candidates=(qualified("equivalent"),),
                allowed_components=("equivalent",),
            )


if __name__ == "__main__":
    unittest.main()
