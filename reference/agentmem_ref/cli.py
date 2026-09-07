"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.cli``."""
import sys
from .runtime import cli as _real
sys.modules[__name__] = _real
