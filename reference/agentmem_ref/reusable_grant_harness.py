"""Compatibility alias -- this module lives at ``agentmem_ref.harness.reusable_grant_harness``."""
import sys
from .harness import reusable_grant_harness as _real
sys.modules[__name__] = _real
