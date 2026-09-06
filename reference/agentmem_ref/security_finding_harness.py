"""Compatibility alias -- this module lives at ``agentmem_ref.harness.security_finding_harness``."""
import sys
from .harness import security_finding_harness as _real
sys.modules[__name__] = _real
