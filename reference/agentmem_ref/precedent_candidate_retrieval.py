"""Compatibility alias -- this module lives at ``agentmem_ref.memory.precedent_candidate_retrieval``."""
import sys
from .memory import precedent_candidate_retrieval as _real
sys.modules[__name__] = _real
