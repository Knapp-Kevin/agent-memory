"""Compatibility alias -- this module lives at ``agentmem_ref.crg.codegenome_profile``."""
import sys
from .crg import codegenome_profile as _real
sys.modules[__name__] = _real
