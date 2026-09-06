"""Compatibility alias -- this module lives at ``agentmem_ref.harness.cedar_policy_comparator``."""
import sys
from .harness import cedar_policy_comparator as _real
sys.modules[__name__] = _real
