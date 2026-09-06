"""Compatibility alias -- this module lives at ``agentmem_ref.harness.derivation_currentness_depth``."""
import sys
from .harness import derivation_currentness_depth as _real
sys.modules[__name__] = _real
