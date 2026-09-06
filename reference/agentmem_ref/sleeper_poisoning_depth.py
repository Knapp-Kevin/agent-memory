"""Compatibility alias -- this module lives at ``agentmem_ref.harness.sleeper_poisoning_depth``."""
import sys
from .harness import sleeper_poisoning_depth as _real
sys.modules[__name__] = _real
