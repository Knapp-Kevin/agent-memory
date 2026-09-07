"""Compatibility alias -- this module lives at ``agentmem_ref.harness.langgraph_lifecycle_comparator``."""
import sys
from .harness import langgraph_lifecycle_comparator as _real
sys.modules[__name__] = _real
