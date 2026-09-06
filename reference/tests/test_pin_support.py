"""Behaviour of the installed-version pin helper used by comparator identity tests."""

from __future__ import annotations

import importlib.metadata
import unittest

from tests import pin_support


class PinSupportTests(unittest.TestCase):
    def test_installed_version_returns_none_for_missing_distribution(self):
        self.assertIsNone(pin_support.installed_version("definitely-not-installed-xyz"))

    def test_pinned_true_only_on_exact_match(self):
        actual = importlib.metadata.version("jsonschema")
        self.assertTrue(pin_support.pinned("jsonschema", actual))
        self.assertFalse(pin_support.pinned("jsonschema", "0.0.0"))
        self.assertFalse(pin_support.pinned("definitely-not-installed-xyz", "1.0.0"))


if __name__ == "__main__":
    unittest.main()
