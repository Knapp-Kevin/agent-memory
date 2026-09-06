"""Digest and sealing helpers for maintenance-run evidence."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from . import receipts


def digest_for(record: dict[str, Any]) -> str:
    payload = deepcopy(record)
    payload.pop("evidence_digest", None)
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def seal(record: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(record)
    result["evidence_digest"] = digest_for(result)
    receipts.validate("maintenance-run-evidence.schema.json", result)
    return result
