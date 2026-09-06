"""Compatibility alias -- this module lives at ``agentmem_ref.harness.systems_characterization``."""
import sys
from .harness import systems_characterization as _real
sys.modules[__name__] = _real
