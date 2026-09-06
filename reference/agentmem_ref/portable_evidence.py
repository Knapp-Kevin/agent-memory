"""Compatibility alias -- this module lives at ``agentmem_ref.core.portable_evidence``."""
import sys
from .core import portable_evidence as _real
sys.modules[__name__] = _real
