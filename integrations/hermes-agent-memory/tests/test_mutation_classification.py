from __future__ import annotations

import unittest

from agent_memory_hermes.mutation import is_potential_durable_mutation, operation_name


class MutationClassificationTests(unittest.TestCase):
    def test_known_read_only_memory_and_skill_calls_are_not_governed(self) -> None:
        for tool, args in (
            ("memory", {"action": "show"}),
            ("memory", {"action": "read"}),
            ("skill_manage", {"action": "list"}),
            ("skill_manage", {"action": "read", "name": "skill-x"}),
        ):
            with self.subTest(tool=tool, args=args):
                self.assertFalse(is_potential_durable_mutation(tool, args))

    def test_known_mutations_and_unknown_future_actions_are_conservative(self) -> None:
        for tool, args in (
            ("memory", {"action": "add"}),
            ("memory", {"action": "replace"}),
            ("memory", {"action": "remove"}),
            ("skill_manage", {"action": "create"}),
            ("skill_manage", {"action": "patch"}),
            ("skill_manage", {"action": "edit"}),
            ("skill_manage", {"action": "delete"}),
            ("skill_manage", {"action": "future_mutation"}),
        ):
            with self.subTest(tool=tool, args=args):
                self.assertTrue(is_potential_durable_mutation(tool, args))

    def test_operation_name_is_stable(self) -> None:
        self.assertEqual(operation_name("memory", {"action": "ADD"}), "add")
        self.assertEqual(operation_name("skill_manage", {"mode": "PATCH"}), "patch")
        self.assertEqual(operation_name("terminal", {"action": "write"}), "not_applicable")


if __name__ == "__main__":
    unittest.main()
