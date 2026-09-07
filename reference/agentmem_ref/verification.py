"""Compatibility alias -- this module lives at ``agentmem_ref.core.verification``."""
import sys
from .core import verification as _real
sys.modules[__name__] = _real
