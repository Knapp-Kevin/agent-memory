"""Compatibility alias -- this module lives at ``agentmem_ref.harness.domain_schema_discovery_harness``."""
import sys
from .harness import domain_schema_discovery_harness as _real
sys.modules[__name__] = _real
