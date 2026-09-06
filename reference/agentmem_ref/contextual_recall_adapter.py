"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.contextual_recall_adapter``."""
import sys
from .runtime import contextual_recall_adapter as _real
sys.modules[__name__] = _real
