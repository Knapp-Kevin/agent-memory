"""Compatibility alias -- this module lives at ``agentmem_ref.contracts.component_failure_probe``."""
import sys
from .contracts import component_failure_probe as _real
sys.modules[__name__] = _real
