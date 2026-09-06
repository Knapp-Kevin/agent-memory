"""Compatibility alias -- this module lives at ``agentmem_ref.crg.codegenome_scope_residue``."""
import sys
from .crg import codegenome_scope_residue as _real
sys.modules[__name__] = _real
