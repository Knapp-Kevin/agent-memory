#!/usr/bin/env python
"""Emit representation-neutral latent predictive-state evidence for issue #137."""

from __future__ import annotations

import json

from agentmem_ref.latent_predictive_state_harness import run_latent_predictive_state_harness


if __name__ == "__main__":
    print(json.dumps(run_latent_predictive_state_harness(), indent=2, sort_keys=True))
