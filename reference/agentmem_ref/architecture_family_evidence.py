"""Compatibility alias -- this module lives at ``agentmem_ref.harness.architecture_family_evidence``."""
import sys
from .harness import architecture_family_evidence as _real
sys.modules[__name__] = _real
