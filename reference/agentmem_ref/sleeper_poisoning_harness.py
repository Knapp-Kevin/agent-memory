"""Compatibility alias -- this module lives at ``agentmem_ref.harness.sleeper_poisoning_harness``."""
import sys
from .harness import sleeper_poisoning_harness as _real
sys.modules[__name__] = _real
