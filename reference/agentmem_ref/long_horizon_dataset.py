"""Compatibility alias -- this module lives at ``agentmem_ref.harness.long_horizon_dataset``."""
import sys
from .harness import long_horizon_dataset as _real
sys.modules[__name__] = _real
