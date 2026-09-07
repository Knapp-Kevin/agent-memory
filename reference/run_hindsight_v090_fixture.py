#!/usr/bin/env python3
"""Execute the exact Hindsight v0.9.0 chunk/document lifecycle fixture for #352.

The script preserves every provider command result before deriving a small set
of factual observations. It intentionally treats provider IDs as provider
identity only; Agent Memory logical identity is never created here.
"""

from __future__ import annotations

import argparse
from importlib import metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

HINDSIGHT_RELEASE = "v0.9.0"
HINDSIGHT_VERSION = "0.9.0"
HINDSIGHT_COMMIT = "b12646f49ec512136b9f709e608524ffed969668"
PROFILE = "agent-memory-qualification"
BANK = "agent-memory-hindsight-v090"
DOCUMENT = "agent-memory-stable-document"
INITIAL_MARKER = "alphacedar731"
REPLACEMENT_MARKER = "omegamaple842"
INITIAL_TEXT = f"{INITIAL_MARKER} retained document state is blue and belongs only to the initial fixture."
REPLACEMENT_TEXT = f"{REPLACEMENT_MARKER} retained document state is green and supersedes the initial fixture."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--license-path", type=Path, required=True)
    parser.add_argument("--source-commit", default=HINDSIGHT_COMMIT)
    parser.add_argument("--port", type=int, default=18888)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    commands: list[dict[str, Any]] = []
    notes: list[str] = []
    package_version = metadata.version("hindsight-embed")
    license_text = args.license_path.read_text(encoding="utf-8")

    raw: dict[str, Any] = {
        "identity": {
            "repository": "vectorize-io/hindsight",
            "release": HINDSIGHT_RELEASE,
            "version": package_version,
            "commit": args.source_commit,
            "license": "MIT" if "MIT License" in license_text else "unverified",
            "license_verified": "MIT License" in license_text,
        },
        "configuration": {
            "llm_provider": "none",
            "retain_extraction_mode": "chunks",
            "external_llm_api_key_present": any(
                bool(os.environ.get(name))
                for name in (
                    "HINDSIGHT_API_LLM_API_KEY",
                    "OPENAI_API_KEY",
                    "ANTHROPIC_API_KEY",
                    "GROQ_API_KEY",
                    "GEMINI_API_KEY",
                )
            ),
            "database": "pg0",
        },
        "fixture": {
            "bank_id": BANK,
            "document_id": DOCUMENT,
            "initial_marker": INITIAL_MARKER,
            "replacement_marker": REPLACEMENT_MARKER,
            "initial_text": INITIAL_TEXT,
            "replacement_text": REPLACEMENT_TEXT,
        },
        "identity_boundary_preserved": True,
        "commands": commands,
        "provider_notes": notes,
    }

    try:
        _create_profile(args.port, commands)
        _run(["hindsight-embed", "-p", PROFILE, "daemon", "start"], commands, "daemon-start")
        _cli(["bank", "create", BANK], commands, "bank-create")

        _retain(INITIAL_TEXT, commands, "initial-retain")
        initial_doc = _cli_json(["document", "get", BANK, DOCUMENT], commands, "initial-document-get")
        initial_list = _cli_json(["document", "list", BANK], commands, "initial-document-list")
        initial_recall = _cli_json(
            ["memory", "recall", BANK, INITIAL_MARKER, "--include-chunks", "--budget", "low"],
            commands,
            "initial-recall",
        )
        raw["initial"] = {
            "document_count": _document_count(initial_list),
            "document_text_matches": _document_text(initial_doc) == INITIAL_TEXT,
            "recall_contains_initial": _contains_provider_content(initial_recall, INITIAL_MARKER),
        }

        _retain(INITIAL_TEXT, commands, "same-key-repeat")
        repeat_doc = _cli_json(["document", "get", BANK, DOCUMENT], commands, "repeat-document-get")
        repeat_list = _cli_json(["document", "list", BANK], commands, "repeat-document-list")
        raw["same_key_repeat"] = {
            "document_count": _document_count(repeat_list),
            "document_text_matches": _document_text(repeat_doc) == INITIAL_TEXT,
        }

        _retain(REPLACEMENT_TEXT, commands, "replacement-retain")
        replacement_doc = _cli_json(
            ["document", "get", BANK, DOCUMENT], commands, "replacement-document-get"
        )
        replacement_list = _cli_json(["document", "list", BANK], commands, "replacement-document-list")
        replacement_recall = _cli_json(
            ["memory", "recall", BANK, REPLACEMENT_MARKER, "--include-chunks", "--budget", "low"],
            commands,
            "replacement-recall",
        )
        old_recall = _cli_json(
            ["memory", "recall", BANK, INITIAL_MARKER, "--include-chunks", "--budget", "low"],
            commands,
            "old-marker-after-replacement",
        )
        raw["replacement"] = {
            "document_count": _document_count(replacement_list),
            "document_text_matches_replacement": _document_text(replacement_doc) == REPLACEMENT_TEXT,
            "recall_contains_replacement": _contains_provider_content(replacement_recall, REPLACEMENT_MARKER),
            "recall_contains_initial": _contains_provider_content(old_recall, INITIAL_MARKER),
        }

        _run(["hindsight-embed", "-p", PROFILE, "daemon", "stop"], commands, "daemon-stop-before-restart")
        _run(["hindsight-embed", "-p", PROFILE, "daemon", "start"], commands, "daemon-restart")
        restart_doc = _cli_json(["document", "get", BANK, DOCUMENT], commands, "restart-document-get")
        restart_list = _cli_json(["document", "list", BANK], commands, "restart-document-list")
        restart_recall = _cli_json(
            ["memory", "recall", BANK, REPLACEMENT_MARKER, "--include-chunks", "--budget", "low"],
            commands,
            "restart-recall",
        )
        raw["restart"] = {
            "daemon_restart_succeeded": True,
            "document_count": _document_count(restart_list),
            "document_text_matches_replacement": _document_text(restart_doc) == REPLACEMENT_TEXT,
            "recall_contains_replacement": _contains_provider_content(restart_recall, REPLACEMENT_MARKER),
        }

        _retain(REPLACEMENT_TEXT, commands, "durable-key-repeat-after-restart")
        durable_doc = _cli_json(["document", "get", BANK, DOCUMENT], commands, "durable-repeat-document-get")
        durable_list = _cli_json(["document", "list", BANK], commands, "durable-repeat-document-list")
        raw["durable_repeat_after_restart"] = {
            "document_count": _document_count(durable_list),
            "document_text_matches_replacement": _document_text(durable_doc) == REPLACEMENT_TEXT,
        }

        delete_result = _cli_json(["document", "delete", BANK, DOCUMENT], commands, "document-delete")
        get_after_delete = _run(
            _cli_command(["document", "get", BANK, DOCUMENT]),
            commands,
            "document-get-after-delete",
            expect_success=False,
        )
        delete_list = _cli_json(["document", "list", BANK], commands, "document-list-after-delete")
        old_after_delete = _cli_json(
            ["memory", "recall", BANK, INITIAL_MARKER, "--include-chunks", "--budget", "low"],
            commands,
            "old-marker-after-delete",
        )
        replacement_after_delete = _cli_json(
            ["memory", "recall", BANK, REPLACEMENT_MARKER, "--include-chunks", "--budget", "low"],
            commands,
            "replacement-marker-after-delete",
        )
        raw["deletion"] = {
            "delete_succeeded": _delete_succeeded(delete_result),
            "get_after_delete_failed": get_after_delete.returncode != 0,
            "document_count": _document_count(delete_list),
            "recall_contains_initial": _contains_provider_content(old_after_delete, INITIAL_MARKER),
            "recall_contains_replacement": _contains_provider_content(
                replacement_after_delete, REPLACEMENT_MARKER
            ),
        }

        _run(
            _cli_command(["bank", "delete", BANK, "--yes"]),
            commands,
            "bank-delete",
            expect_success=False,
        )
    except Exception as exc:
        notes.append(f"fixture execution stopped with {type(exc).__name__}: {exc}")
        raw["execution_error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        _run(
            ["hindsight-embed", "-p", PROFILE, "daemon", "stop"],
            commands,
            "final-daemon-stop",
            expect_success=False,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return 0


def _create_profile(port: int, commands: list[dict[str, Any]]) -> None:
    env_values = [
        "HINDSIGHT_API_LLM_PROVIDER=none",
        "HINDSIGHT_API_SKIP_LLM_VERIFICATION=true",
        "HINDSIGHT_API_RETAIN_EXTRACTION_MODE=chunks",
        "HINDSIGHT_API_ENABLE_OBSERVATIONS=false",
        "HINDSIGHT_API_ENABLE_AUTO_CONSOLIDATION=false",
        "HINDSIGHT_API_ENABLE_RERANKING=false",
        "HINDSIGHT_API_ENABLE_GRAPH_RETRIEVAL=false",
        "HINDSIGHT_API_ENABLE_TEMPORAL_RETRIEVAL=false",
        "HINDSIGHT_API_MCP_ENABLED=false",
        "HINDSIGHT_EMBED_API_DATABASE_URL=pg0://agent-memory-hindsight-v090",
        "HINDSIGHT_API_DATABASE_URL=pg0://agent-memory-hindsight-v090",
        "HINDSIGHT_EMBED_API_VERSION=0.9.0",
        "HINDSIGHT_EMBED_CLI_VERSION=0.9.0",
    ]
    command = ["hindsight-embed", "profile", "create", PROFILE, "--port", str(port)]
    for value in env_values:
        command.extend(["--env", value])
    _run(command, commands, "profile-create")


def _retain(content: str, commands: list[dict[str, Any]], name: str) -> None:
    _cli_json(
        ["memory", "retain", BANK, content, "--doc-id", DOCUMENT, "--timestamp", "unset"],
        commands,
        name,
    )


def _cli(args: list[str], commands: list[dict[str, Any]], name: str) -> subprocess.CompletedProcess[str]:
    return _run(_cli_command(args), commands, name)


def _cli_json(args: list[str], commands: list[dict[str, Any]], name: str) -> Any:
    result = _run(_cli_command(args), commands, name)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{name} did not emit JSON: {result.stdout[:500]!r}") from exc


def _cli_command(args: list[str]) -> list[str]:
    return ["hindsight-embed", "-p", PROFILE, "-o", "json", *args]


def _run(
    command: list[str],
    commands: list[dict[str, Any]],
    name: str,
    *,
    expect_success: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=240)
    except Exception as exc:
        commands.append(
            {
                "name": name,
                "command": command,
                "returncode": None,
                "stdout": "",
                "stderr": "",
                "exception": f"{type(exc).__name__}: {exc}",
            }
        )
        if expect_success:
            raise
        return subprocess.CompletedProcess(command, 255, "", str(exc))
    commands.append(
        {
            "name": name,
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    )
    if expect_success and result.returncode != 0:
        raise RuntimeError(
            f"{name} failed with exit {result.returncode}: {result.stderr[-1000:]}"
        )
    return result


def _document_count(value: Any) -> int:
    if isinstance(value, dict):
        total = value.get("total")
        if isinstance(total, int):
            return total
        items = value.get("items")
        if isinstance(items, list):
            return len(items)
    if isinstance(value, list):
        return len(value)
    return -1


def _document_text(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    for key in ("original_text", "text", "content"):
        candidate = value.get(key)
        if isinstance(candidate, str):
            return candidate
    return None


def _delete_succeeded(value: Any) -> bool:
    if isinstance(value, dict):
        result = value.get("success")
        if isinstance(result, bool):
            return result
        status = value.get("status")
        if isinstance(status, str):
            return status.lower() in {"ok", "success", "deleted"}
    return False


def _contains_provider_content(value: Any, marker: str) -> bool:
    marker = marker.lower()

    def walk(item: Any, *, parent_key: str = "") -> bool:
        if isinstance(item, str):
            # Avoid treating echoed request/query fields as retrieved content.
            if parent_key in {"query", "request", "input", "search_query"}:
                return False
            return marker in item.lower()
        if isinstance(item, list):
            return any(walk(child, parent_key=parent_key) for child in item)
        if isinstance(item, dict):
            return any(walk(child, parent_key=str(key).lower()) for key, child in item.items())
        return False

    return walk(value)


if __name__ == "__main__":
    sys.exit(main())
