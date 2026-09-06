"""Version-bound component capability qualification tests for #300."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.qualification import (  # noqa: E402
    AdapterResult,
    QualificationError,
    QualificationRecord,
    QualificationRuntime,
    QualificationSubject,
    StaleQualificationError,
    qualification_from_adapter_results,
)

ROOT = Path(__file__).resolve().parents[2]


class ComponentQualificationTests(unittest.TestCase):
    def _subject(self, *, component_version: str = "d2578729") -> QualificationSubject:
        return QualificationSubject(
            component_id="codegenome",
            component_version=component_version,
            implementation_ref=f"MythologIQ-Labs-LLC/CodeGenome@{component_version}",
            capability_id="code_graph_traversal",
            capability_version="1.0",
            adapter_id="codegenome-cli",
            adapter_version="1.0.0",
            qualification_profile_id="code-graph-traversal",
            qualification_profile_version="1.0.0",
        )

    def _runtime(self, *, config: str = "a") -> QualificationRuntime:
        return QualificationRuntime(
            configuration_digest="sha256:" + config * 64,
            fixture_id="code-reality-v1",
            fixture_digest="sha256:" + "b" * 64,
            dependency_refs=("rust:stable",),
            runtime_refs=("ubuntu-latest",),
        )

    def _adapter_result(
        self,
        *,
        currentness: str = "current",
        failure_result: str = "none",
        operation: str = "impact_downstream",
    ) -> AdapterResult:
        return AdapterResult(
            subject=self._subject(),
            operation=operation,
            runtime_identity="codegenome-cli:test",
            input_refs=("fixture:main.rs:8",),
            raw_provider_refs=("artifact:raw-codegenome.json",),
            normalized_refs=("artifact:normalized.json",),
            currentness=currentness,
            failure_result=failure_result,
            trace_ref="trace:1",
        )

    def _record(
        self,
        *,
        earned: str = "evidence_proven",
        result: AdapterResult | None = None,
    ) -> QualificationRecord:
        subject = self._subject()
        result = result or self._adapter_result()
        return qualification_from_adapter_results(
            subject=subject,
            runtime=self._runtime(),
            license_id="MIT",
            license_ref="CodeGenome/LICENSE@d2578729",
            use_posture="runtime_allowed",
            results=(result,),
            checks=(
                ("target-file-identity", True, "artifact:normalized.json"),
                ("direction-fidelity", True, "artifact:normalized.json"),
            ),
            artifact_digests=("sha256:" + "c" * 64,),
            maturity_before="runtime_wired",
            profile_maturity_ceiling="evidence_proven",
            earned_maturity=earned,
        )

    def test_record_validates_against_machine_readable_schema(self):
        schema = json.loads((ROOT / "schemas" / "component-capability-qualification.schema.json").read_text())
        validator = jsonschema.Draft202012Validator(schema)
        record = self._record().to_dict()
        self.assertEqual(record["schema_version"], "1.1.0")
        errors = list(validator.iter_errors(record))
        self.assertEqual(errors, [], [error.message for error in errors])

    def test_adapter_currentness_and_failure_result_are_machine_readable(self):
        record = self._record(
            result=self._adapter_result(
                currentness="unavailable",
                failure_result="provider_unavailable",
                operation="provider_availability_probe",
            )
        )
        evidence = record.to_dict()["evidence"]
        self.assertEqual(len(evidence["adapter_results"]), 1)
        adapter = evidence["adapter_results"][0]
        self.assertEqual(adapter["currentness"], "unavailable")
        self.assertEqual(adapter["failure_result"], "provider_unavailable")
        self.assertEqual(adapter["authority_effect"], "none")
        self.assertEqual(record.failure_results, ("provider_unavailable",))

    def test_adapter_requires_currentness_and_failure_result(self):
        with self.assertRaises(ValueError):
            AdapterResult(
                subject=self._subject(),
                operation="query",
                runtime_identity="runtime",
                input_refs=(),
                raw_provider_refs=("raw",),
                normalized_refs=("normalized",),
                currentness="",
                failure_result="none",
                trace_ref="trace",
            )
        with self.assertRaises(ValueError):
            AdapterResult(
                subject=self._subject(),
                operation="query",
                runtime_identity="runtime",
                input_refs=(),
                raw_provider_refs=("raw",),
                normalized_refs=("normalized",),
                currentness="current",
                failure_result="",
                trace_ref="trace",
            )

    def test_component_version_drift_invalidates_old_qualification(self):
        record = self._record()
        changed = self._subject(component_version="changed-version")
        with self.assertRaises(StaleQualificationError):
            record.assert_applicable(changed, self._runtime())

    def test_runtime_configuration_drift_invalidates_old_qualification(self):
        record = self._record()
        with self.assertRaises(StaleQualificationError):
            record.assert_applicable(self._subject(), self._runtime(config="d"))

    def test_exact_subject_and_runtime_remain_applicable(self):
        record = self._record()
        record.assert_applicable(self._subject(), self._runtime())

    def test_adapter_requires_raw_and_normalized_evidence(self):
        with self.assertRaises(ValueError):
            AdapterResult(
                subject=self._subject(),
                operation="query",
                runtime_identity="runtime",
                input_refs=(),
                raw_provider_refs=(),
                normalized_refs=("normalized",),
                currentness="current",
                failure_result="none",
                trace_ref="trace",
            )

    def test_runtime_wired_can_earn_evidence_proven_within_profile_ceiling(self):
        record = self._record(earned="evidence_proven")
        self.assertEqual(record.maturity_before, "runtime_wired")
        self.assertEqual(record.profile_maturity_ceiling, "evidence_proven")
        self.assertEqual(record.earned_maturity, "evidence_proven")

    def test_qualification_cannot_exceed_profile_maturity_ceiling(self):
        with self.assertRaises(QualificationError):
            QualificationRecord(
                subject=self._subject(),
                runtime=self._runtime(),
                license_id="MIT",
                license_ref="license",
                use_posture="runtime_allowed",
                operations=("query",),
                raw_provider_refs=("raw",),
                normalized_refs=("normalized",),
                checks=(("positive", True, "evidence"),),
                artifact_digests=("sha256:" + "e" * 64,),
                maturity_before="runtime_wired",
                profile_maturity_ceiling="evidence_proven",
                earned_maturity="reference_qualified",
            )

    def test_reference_qualified_requires_explicit_ceiling_and_all_profile_checks(self):
        with self.assertRaises(QualificationError):
            QualificationRecord(
                subject=self._subject(),
                runtime=self._runtime(),
                license_id="MIT",
                license_ref="license",
                use_posture="runtime_allowed",
                operations=("query",),
                raw_provider_refs=("raw",),
                normalized_refs=("normalized",),
                checks=(("positive", True, "evidence"), ("stale-version", False, "negative")),
                artifact_digests=("sha256:" + "f" * 64,),
                maturity_before="evidence_proven",
                profile_maturity_ceiling="reference_qualified",
                earned_maturity="reference_qualified",
                adapter_results=(self._adapter_result(),),
            )

    def test_reference_qualified_requires_runtime_allowed_source_rights(self):
        with self.assertRaises(QualificationError):
            QualificationRecord(
                subject=self._subject(),
                runtime=self._runtime(),
                license_id="restricted",
                license_ref="license",
                use_posture="comparator_only",
                operations=("query",),
                raw_provider_refs=("raw",),
                normalized_refs=("normalized",),
                checks=(("positive", True, "evidence"),),
                artifact_digests=("sha256:" + "f" * 64,),
                maturity_before="evidence_proven",
                profile_maturity_ceiling="reference_qualified",
                earned_maturity="reference_qualified",
                adapter_results=(self._adapter_result(),),
            )

    def test_reference_qualified_requires_reconstructable_adapter_results(self):
        with self.assertRaisesRegex(QualificationError, "adapter-result evidence"):
            QualificationRecord(
                subject=self._subject(),
                runtime=self._runtime(),
                license_id="MIT",
                license_ref="license",
                use_posture="runtime_allowed",
                operations=("query",),
                raw_provider_refs=("raw",),
                normalized_refs=("normalized",),
                checks=(("positive", True, "evidence"),),
                artifact_digests=("sha256:" + "f" * 64,),
                maturity_before="evidence_proven",
                profile_maturity_ceiling="reference_qualified",
                earned_maturity="reference_qualified",
            )

    def test_qualification_and_adapter_never_grant_authority(self):
        record = self._record()
        self.assertEqual(record.authority_effect, "none")
        self.assertEqual(record.to_dict()["result"]["authority_effect"], "none")
        self.assertEqual(record.to_dict()["evidence"]["adapter_results"][0]["authority_effect"], "none")

    def test_qualification_is_capability_specific_not_component_wide(self):
        record = self._record()
        self.assertEqual(record.subject.capability_id, "code_graph_traversal")
        self.assertNotEqual(record.subject.capability_id, "vector_candidate_retrieval")


if __name__ == "__main__":
    unittest.main()
