"""Compatibility alias -- this module lives at ``agentmem_ref.harness.autonomous_maintenance_harness``."""
import sys
from .harness import autonomous_maintenance_harness as _real
sys.modules[__name__] = _real
