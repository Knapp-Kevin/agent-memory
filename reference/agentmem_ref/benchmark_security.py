"""Compatibility alias -- this module lives at ``agentmem_ref.harness.benchmark_security``."""
import sys
from .harness import benchmark_security as _real
sys.modules[__name__] = _real
