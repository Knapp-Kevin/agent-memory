"""Compatibility alias -- this module lives at ``agentmem_ref.harness.long_horizon_benchmark``."""
import sys
from .harness import long_horizon_benchmark as _real
sys.modules[__name__] = _real
