"""Compatibility alias -- this module lives at ``agentmem_ref.harness.maf_lifecycle_comparator``."""
import sys
from .harness import maf_lifecycle_comparator as _real
sys.modules[__name__] = _real
