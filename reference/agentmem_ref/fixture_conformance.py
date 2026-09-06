"""Compatibility alias -- this module lives at ``agentmem_ref.harness.fixture_conformance``."""
import sys
from .harness import fixture_conformance as _real
sys.modules[__name__] = _real
