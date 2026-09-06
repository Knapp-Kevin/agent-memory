"""Compatibility alias -- this module lives at ``agentmem_ref.memory.agent_manifest_external_evidence``."""
import sys
from .memory import agent_manifest_external_evidence as _real
sys.modules[__name__] = _real
