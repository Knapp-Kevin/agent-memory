"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.write_claims``."""
import sys
from .runtime import write_claims as _real
sys.modules[__name__] = _real
