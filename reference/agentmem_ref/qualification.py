"""Compatibility alias -- this module lives at ``agentmem_ref.contracts.qualification``."""
import sys
from .contracts import qualification as _real
sys.modules[__name__] = _real
