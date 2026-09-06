"""Compatibility alias -- this module lives at ``agentmem_ref.contracts.resource_provider_substitution``."""
import sys
from .contracts import resource_provider_substitution as _real
sys.modules[__name__] = _real
