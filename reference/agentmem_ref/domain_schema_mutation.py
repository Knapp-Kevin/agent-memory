"""Compatibility alias -- this module lives at ``agentmem_ref.memory.domain_schema_mutation``."""
import sys
from .memory import domain_schema_mutation as _real
sys.modules[__name__] = _real
