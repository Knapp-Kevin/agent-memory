"""Compatibility alias -- this module lives at ``agentmem_ref.contracts.memos_qualification``."""
import sys
from .contracts import memos_qualification as _real
sys.modules[__name__] = _real
