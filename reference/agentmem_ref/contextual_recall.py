"""Compatibility alias -- this module lives at ``agentmem_ref.core.contextual_recall``."""
import sys
from .core import contextual_recall as _real
sys.modules[__name__] = _real
