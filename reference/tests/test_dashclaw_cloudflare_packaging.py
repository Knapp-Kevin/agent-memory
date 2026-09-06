from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PREPARE_PATH = REPO_ROOT / "examples" / "cloudflare-dashclaw-provider" / "prepare.py"


def _load_prepare_module():
    spec = importlib.util.spec_from_file_location("dashclaw_cloudflare_prepare", PREPARE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Cloudflare prepare module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DashClawCloudflarePackagingTests(unittest.TestCase):
    def test_prepared_provider_uses_canonical_sources_and_imports_without_runtime_dependencies(self) -> None:
        prepare = _load_prepare_module()
        rendered, manifest = prepare._render_sources()

        self.assertEqual(
            set(rendered),
            {"policy.py", "dashclaw_external_verdict.py", "dashclaw_authority.py"},
        )
        self.assertEqual(set(manifest), set(rendered))
        self.assertIn("if TYPE_CHECKING:\n    from .adapter import GovernedMemoryAdapter", rendered["dashclaw_external_verdict.py"])
        self.assertNotIn("\nfrom .adapter import GovernedMemoryAdapter\n", rendered["dashclaw_external_verdict.py"])

        with tempfile.TemporaryDirectory(prefix="dashclaw-cf-test-") as temp:
            root = Path(temp)
            prepared_manifest = prepare._write_package(root / "agentmem_ref")
            prepare._import_check(root)

        self.assertEqual(prepared_manifest, manifest)

    def test_import_check_leaves_canonical_modules_as_it_found_them(self) -> None:
        """Regression: the prepared copies must not evict the canonical package.

        `_import_check` previously purged every `agentmem_ref` module from
        `sys.modules` without restoring it. Because this test sorts before
        `test_temporal_trust`, a later `mock.patch("agentmem_ref.temporal_trust.
        public_key_digest")` re-imported a fresh module and patched that, while
        the already-bound `evaluate_attestation_trust` still closed over the old
        module's globals -- so the real digest ran against a dummy key and five
        cases failed with `public_key must be Ed25519PublicKey`.

        Module *identity* is the invariant, not merely presence.
        """
        import agentmem_ref.temporal_trust as canonical_trust
        import agentmem_ref.policy as canonical_policy

        prepare = _load_prepare_module()
        before = {
            name: module
            for name, module in sys.modules.items()
            if name == "agentmem_ref" or name.startswith("agentmem_ref.")
        }

        with tempfile.TemporaryDirectory(prefix="dashclaw-cf-restore-") as temp:
            root = Path(temp)
            prepare._write_package(root / "agentmem_ref")
            prepare._import_check(root)

        for name, module in before.items():
            self.assertIn(name, sys.modules, f"{name} was evicted by _import_check")
            self.assertIs(sys.modules[name], module, f"{name} identity changed")

        self.assertIs(sys.modules["agentmem_ref.temporal_trust"], canonical_trust)
        self.assertIs(sys.modules["agentmem_ref.policy"], canonical_policy)
        self.assertNotIn(str(root), sys.path)

    def test_patching_still_works_after_import_check(self) -> None:
        """The end-to-end shape of the failure, without depending on test order."""
        from unittest.mock import patch

        import agentmem_ref.temporal_trust as trust

        prepare = _load_prepare_module()
        with tempfile.TemporaryDirectory(prefix="dashclaw-cf-patch-") as temp:
            root = Path(temp)
            prepare._write_package(root / "agentmem_ref")
            prepare._import_check(root)

        sentinel = "sha256:" + "ab" * 32
        with patch("agentmem_ref.temporal_trust.public_key_digest", return_value=sentinel):
            self.assertEqual(trust.public_key_digest(object()), sentinel)


if __name__ == "__main__":
    unittest.main()
