"""Compatibility alias -- this module lives at ``agentmem_ref.crg.codegenome_cognitive_mesh``."""
import sys
from .crg import codegenome_cognitive_mesh as _real
sys.modules[__name__] = _real
