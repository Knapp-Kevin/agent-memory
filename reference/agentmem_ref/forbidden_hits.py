"""Compatibility alias -- this module lives at ``agentmem_ref.harness.forbidden_hits``."""
import sys
from .harness import forbidden_hits as _real
sys.modules[__name__] = _real
