"""Compatibility alias -- this module lives at ``agentmem_ref.crg.code_graph_qualification``."""
import sys
from .crg import code_graph_qualification as _real
sys.modules[__name__] = _real
