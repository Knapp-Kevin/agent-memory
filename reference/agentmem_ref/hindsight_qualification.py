"""Compatibility alias -- this module lives at ``agentmem_ref.contracts.hindsight_qualification``."""
import sys
from .contracts import hindsight_qualification as _real
sys.modules[__name__] = _real
