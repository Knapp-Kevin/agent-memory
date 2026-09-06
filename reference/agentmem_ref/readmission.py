"""Compatibility alias -- this module lives at ``agentmem_ref.core.readmission``."""
import sys
from .core import readmission as _real
sys.modules[__name__] = _real
