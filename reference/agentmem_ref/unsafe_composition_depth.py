"""Compatibility alias -- this module lives at ``agentmem_ref.harness.unsafe_composition_depth``."""
import sys
from .harness import unsafe_composition_depth as _real
sys.modules[__name__] = _real
