"""Compatibility alias -- this module lives at ``agentmem_ref.harness.logical_state_algebra_pressure``."""
import sys
from .harness import logical_state_algebra_pressure as _real
sys.modules[__name__] = _real
