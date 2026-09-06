"""Compatibility alias -- this module lives at ``agentmem_ref.contracts.evolveai_profile``."""
import sys
from .contracts import evolveai_profile as _real
sys.modules[__name__] = _real
