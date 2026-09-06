"""Installed-distribution version helpers for pin-identity tests (not collected as a test)."""

from __future__ import annotations

import importlib.metadata


def installed_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def pinned(distribution: str, expected: str) -> bool:
    return installed_version(distribution) == expected
