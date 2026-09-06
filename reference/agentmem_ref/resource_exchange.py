"""Compatibility alias -- this module lives at ``agentmem_ref.contracts.resource_exchange``."""
import sys
from .contracts import resource_exchange as _real
sys.modules[__name__] = _real
