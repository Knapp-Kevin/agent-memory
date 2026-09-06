import hashlib
import unittest

from agentmem_ref.uor_content_reference import (
    UorBindingUnavailable,
    UorInvalidInput,
    default_profile_metadata,
    evaluate_json_content_reference,
)


def fake_address(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


class UorContentReferenceTests(unittest.TestCase):
    def test_generated_reference_is_non_authoritative(self):
        evidence = evaluate_json_content_reference(b'{"a":1}', address_fn=fake_address, binding_name="fixture", binding_version="0")
        self.assertEqual(evidence["status"], "generated")
        self.assertTrue(evidence["content_identity_only"])
        self.assertEqual(evidence["authority_effect"], "none")
        self.assertFalse(evidence["can_create_logical_memory_identity"])
        self.assertFalse(evidence["can_create_lifecycle_currentness"])
        self.assertFalse(evidence["can_admit_recall"])
        self.assertFalse(evidence["can_satisfy_pama_mutation_authority"])
        self.assertFalse(evidence["ordinary_agent_memory_requires_uor_runtime"])

    def test_match_mismatch_and_malformed_claim(self):
        label = fake_address(b'{"a":1}')
        verified = evaluate_json_content_reference(b'{"a":1}', address_fn=fake_address, binding_name="fixture", binding_version="0", claimed_label=label)
        self.assertEqual(verified["status"], "verified")
        mismatch = evaluate_json_content_reference(b'{"a":2}', address_fn=fake_address, binding_name="fixture", binding_version="0", claimed_label=label)
        self.assertEqual(mismatch["status"], "mismatch")
        self.assertFalse(mismatch["failure"]["fail_open"])
        malformed = evaluate_json_content_reference(b'{"a":1}', address_fn=fake_address, binding_name="fixture", binding_version="0", claimed_label="sha256:not-a-digest")
        self.assertEqual(malformed["status"], "invalid_label")
        self.assertFalse(malformed["failure"]["fail_open"])

    def test_optional_failure_modes(self):
        metadata = default_profile_metadata()
        metadata["profile_version"] = "999.0.0"
        unsupported = evaluate_json_content_reference(b'{"a":1}', address_fn=fake_address, binding_name="fixture", binding_version="0", profile_metadata=metadata)
        self.assertEqual(unsupported["status"], "unsupported")
        metadata = default_profile_metadata()
        metadata["future_field"] = "unknown"
        unknown = evaluate_json_content_reference(b'{"a":1}', address_fn=fake_address, binding_name="fixture", binding_version="0", profile_metadata=metadata)
        self.assertEqual(unknown["status"], "unsupported")

        def unavailable(_: bytes) -> str:
            raise UorBindingUnavailable("missing optional runtime")
        unavailable_result = evaluate_json_content_reference(b'{"a":1}', address_fn=unavailable, binding_name="fixture", binding_version="0")
        self.assertEqual(unavailable_result["status"], "unavailable")
        self.assertFalse(unavailable_result["ordinary_agent_memory_requires_uor_runtime"])

        def invalid(_: bytes) -> str:
            raise UorInvalidInput("invalid JSON")
        invalid_result = evaluate_json_content_reference(b'{', address_fn=invalid, binding_name="fixture", binding_version="0")
        self.assertEqual(invalid_result["status"], "invalid_input")
        self.assertFalse(invalid_result["failure"]["fail_open"])


if __name__ == "__main__":
    unittest.main()
