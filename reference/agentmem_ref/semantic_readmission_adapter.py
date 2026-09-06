"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.semantic_readmission_adapter``."""
import sys
from .runtime import semantic_readmission_adapter as _real
sys.modules[__name__] = _real
