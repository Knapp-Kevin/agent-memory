"""Compatibility alias -- this module lives at ``agentmem_ref.memory.uor_content_reference``."""
import sys
from .memory import uor_content_reference as _real
sys.modules[__name__] = _real
