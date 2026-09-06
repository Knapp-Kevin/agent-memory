"""Compatibility alias -- this module lives at ``agentmem_ref.harness.operational_memory_benchmark``."""
import sys
from .harness import operational_memory_benchmark as _real
sys.modules[__name__] = _real
