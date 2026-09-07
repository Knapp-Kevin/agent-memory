"""Compatibility alias -- this module lives at ``agentmem_ref.harness.visibility_characterization``."""
import sys
from .harness import visibility_characterization as _real
sys.modules[__name__] = _real
