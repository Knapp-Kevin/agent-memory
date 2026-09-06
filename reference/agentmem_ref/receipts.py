"""Compatibility alias -- this module lives at ``agentmem_ref.core.receipts``."""
import sys
from .core import receipts as _real
sys.modules[__name__] = _real
