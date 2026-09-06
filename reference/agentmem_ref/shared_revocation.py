"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.shared_revocation``."""
import sys
from .runtime import shared_revocation as _real
sys.modules[__name__] = _real
