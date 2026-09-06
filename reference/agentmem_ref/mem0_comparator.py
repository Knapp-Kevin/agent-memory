"""Compatibility alias -- this module lives at ``agentmem_ref.harness.mem0_comparator``."""
import sys
from .harness import mem0_comparator as _real
sys.modules[__name__] = _real
