"""Compatibility alias -- this module lives at ``agentmem_ref.core.evidence_qualification``."""
import sys
from .core import evidence_qualification as _real
sys.modules[__name__] = _real
