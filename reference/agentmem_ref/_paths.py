"""Package and repository roots, computed once at the package top level.

Every module that needs the repository root (fixtures, schemas, policies) or
the reference-tree root imports these names instead of computing
``Path(__file__).resolve().parents[N]`` -- which is coupled to how deep the
importing module happens to live, and shifts silently when a module moves
into a subpackage. This file stays at the top of ``agentmem_ref`` so the
depths below are stable by construction.
"""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent          # reference/agentmem_ref
REFERENCE_ROOT = PACKAGE_ROOT.parent                     # reference/
REPO_ROOT = REFERENCE_ROOT.parent                        # repository root

PACKAGE_NAME = "agentmem_ref"                            # top-level name, for importlib.resources
