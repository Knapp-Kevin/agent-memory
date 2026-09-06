from __future__ import annotations

import importlib.metadata
import unittest

from agent.memory_provider import MemoryProvider
from agent_memory_hermes.provider import AgentMemoryProvider


class ExactHermesContractTests(unittest.TestCase):
    def test_provider_subclasses_exact_hermes_memory_provider(self) -> None:
        self.assertTrue(issubclass(AgentMemoryProvider, MemoryProvider))
        provider = AgentMemoryProvider()
        self.assertEqual(provider.name, "agent-memory")
        self.assertEqual(provider.get_tool_schemas(), [])

    def test_installed_entry_points_use_supported_hermes_groups(self) -> None:
        plugin = {
            ep.name: ep.value
            for ep in importlib.metadata.entry_points(group="hermes_agent.plugins")
        }
        provider = {
            ep.name: ep.value
            for ep in importlib.metadata.entry_points(group="hermes_agent.memory_providers")
        }
        self.assertEqual(plugin["agent-memory"], "agent_memory_hermes.safe_plugin:register")
        self.assertEqual(provider["agent-memory"], "agent_memory_hermes.provider:register_memory")


if __name__ == "__main__":
    unittest.main()
