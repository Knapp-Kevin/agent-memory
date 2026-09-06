"""Compatibility alias -- this module lives at ``agentmem_ref.harness.security_finding_depth``."""
import sys
from .harness import security_finding_depth as _real
sys.modules[__name__] = _real
