"""Compatibility alias -- this module lives at ``agentmem_ref.harness.security_evidence_depth``."""
import sys
from .harness import security_evidence_depth as _real
sys.modules[__name__] = _real
