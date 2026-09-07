#!/usr/bin/env python3
"""Execute bidirectional Hindsight v0.9.0 <-> MemOS v2.0.17 resource copies.

This fixture captures provider-native direct readback before and after each copy.
It deliberately retains the source resource and does not exercise cross-domain
authority; cross-domain receipt composition is covered by the reference contract
tests against the canonical ADR-022 schema.
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

HINDSIGHT_VERSION = "0.9.0"
HINDSIGHT_COMMIT = "b12646f49ec512136b9f709e608524ffed969668"
MEMOS_VERSION = "2.0.17"
MEMOS_COMMIT = "d3d1bcfaff65f31b621d58bc236ece6d1e0da5ab"
DOMAIN = "memory-domain:project:federated-exchange-fixture"
PROVENANCE = [
    "source:fixture:federated-resource-exchange-v1",
    "issue:https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/358",
]
H2M_LOGICAL_ID = "agent-memory:resource:federated-hindsight-to-memos"
M2H_LOGICAL_ID = "agent-memory:resource:federated-memos-to-hindsight"
H2M_CONTENT = "amber-river-481 exact resource bytes move from Hindsight to MemOS without becoming provider identity."
M2H_CONTENT = "cobalt-grove-592 exact resource bytes move from MemOS to Hindsight without becoming provider identity."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--memos-package-root", type=Path, required=True)
    parser.add_argument("--memos-h2m-home", type=Path, required=True)
    parser.add_argument("--memos-m2h-home", type=Path, required=True)
    parser.add_argument("--hindsight-source-commit", default=HINDSIGHT_COMMIT)
    parser.add_argument("--memos-source-commit", default=MEMOS_COMMIT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    commands: list[dict[str, Any]] = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = args.output.parent / "endpoint-evidence"
    temp_dir.mkdir(parents=True, exist_ok=True)

    raw: dict[str, Any] = {
        "identity": {
            "hindsight": {
                "component_id": "hindsight-v0.9.0",
                "version": metadata.version("hindsight-embed"),
                "source_commit": args.hindsight_source_commit,
            },
            "memos": {
                "component_id": "memos-local-plugin-v2.0.17",
                "version": MEMOS_VERSION,
                "source_commit": args.memos_source_commit,
            },
        },
        "exchange_boundary": {
            "source_domain_refs": [DOMAIN],
            "destination_domain_refs": [DOMAIN],
            "provenance_refs": PROVENANCE,
            "cross_domain_authority_exercised": False,
            "destructive_cutover_exercised": False,
        },
        "commands": commands,
        "authority_effect": "none",
    }

    try:
        if raw["identity"]["hindsight"]["version"] != HINDSIGHT_VERSION:
            raise RuntimeError("unexpected installed Hindsight version")
        memos_pkg = json.loads((args.memos_package_root / "package.json").read_text(encoding="utf-8"))
        if memos_pkg.get("name") != "@memtensor/memos-local-plugin" or memos_pkg.get("version") != MEMOS_VERSION:
            raise RuntimeError("unexpected installed MemOS package identity")

        # Direction 1: Hindsight source -> MemOS target.
        h2m_profile = "agent-memory-exchange-h2m-source"
        h2m_bank = "agent-memory-exchange-h2m-source"
        h2m_doc = "hindsight-native-h2m-source-document"
        _create_profile(h2m_profile, 18890, "agent-memory-exchange-h2m-source", commands)
        _daemon(h2m_profile, "start", commands, "h2m-source-daemon-start")
        _h_cli_json(h2m_profile, ["bank", "create", h2m_bank], commands, "h2m-source-bank-create")
        _h_cli_json(
            h2m_profile,
            ["memory", "retain", h2m_bank, H2M_CONTENT, "--doc-id", h2m_doc, "--timestamp", "unset"],
            commands,
            "h2m-source-retain",
        )
        h2m_source_before = _h_cli_json(
            h2m_profile, ["document", "get", h2m_bank, h2m_doc], commands, "h2m-source-read-before"
        )
        h2m_source_text = _document_text(h2m_source_before)
        h2m_target_trace = "memos-native-h2m-target-trace"
        h2m_target_file = temp_dir / "memos-h2m-target.json"
        _memos_endpoint(
            args,
            action="write-read",
            home=args.memos_h2m_home,
            trace_id=h2m_target_trace,
            content=h2m_source_text or "",
            output=h2m_target_file,
            commands=commands,
            name="h2m-target-memos-write-read",
        )
        h2m_target = json.loads(h2m_target_file.read_text(encoding="utf-8"))
        h2m_source_after = _h_cli_json(
            h2m_profile, ["document", "get", h2m_bank, h2m_doc], commands, "h2m-source-read-after-target"
        )
        _daemon(h2m_profile, "stop", commands, "h2m-source-daemon-stop", expect_success=False)

        raw["hindsight_to_memos"] = {
            "logical_resource_id": H2M_LOGICAL_ID,
            "representation_kind": "text/plain; charset=utf-8",
            "content": H2M_CONTENT,
            "source_domain_refs": [DOMAIN],
            "destination_domain_refs": [DOMAIN],
            "provenance_refs": PROVENANCE,
            "source": {
                "component_id": "hindsight-v0.9.0",
                "component_version": HINDSIGHT_VERSION,
                "native_resource_id": f"hindsight-document:{h2m_bank}/{h2m_doc}",
                "runtime_ref": "hindsight-embed:0.9.0:pg0",
                "readback_before": h2m_source_text,
                "readback_after_target": _document_text(h2m_source_after),
            },
            "target": {
                **h2m_target.get("provider", {}),
                "readback": h2m_target.get("readback"),
                "write_import_result": h2m_target.get("import_result"),
            },
            "source_retained": _document_text(h2m_source_after) == H2M_CONTENT,
            "target_readback_matches": h2m_target.get("readback") == H2M_CONTENT,
        }

        # Direction 2: MemOS source -> Hindsight target.
        m2h_source_trace = "memos-native-m2h-source-trace"
        m2h_source_file = temp_dir / "memos-m2h-source.json"
        _memos_endpoint(
            args,
            action="write-read",
            home=args.memos_m2h_home,
            trace_id=m2h_source_trace,
            content=M2H_CONTENT,
            output=m2h_source_file,
            commands=commands,
            name="m2h-source-memos-write-read",
        )
        m2h_source = json.loads(m2h_source_file.read_text(encoding="utf-8"))
        m2h_profile = "agent-memory-exchange-m2h-target"
        m2h_bank = "agent-memory-exchange-m2h-target"
        m2h_doc = "hindsight-native-m2h-target-document"
        _create_profile(m2h_profile, 18891, "agent-memory-exchange-m2h-target", commands)
        _daemon(m2h_profile, "start", commands, "m2h-target-daemon-start")
        _h_cli_json(m2h_profile, ["bank", "create", m2h_bank], commands, "m2h-target-bank-create")
        _h_cli_json(
            m2h_profile,
            [
                "memory",
                "retain",
                m2h_bank,
                str(m2h_source.get("readback") or ""),
                "--doc-id",
                m2h_doc,
                "--timestamp",
                "unset",
            ],
            commands,
            "m2h-target-retain",
        )
        m2h_target = _h_cli_json(
            m2h_profile, ["document", "get", m2h_bank, m2h_doc], commands, "m2h-target-read"
        )
        m2h_target_text = _document_text(m2h_target)
        m2h_source_after_file = temp_dir / "memos-m2h-source-after.json"
        _memos_endpoint(
            args,
            action="read",
            home=args.memos_m2h_home,
            trace_id=m2h_source_trace,
            content=None,
            output=m2h_source_after_file,
            commands=commands,
            name="m2h-source-memos-read-after-target",
        )
        m2h_source_after = json.loads(m2h_source_after_file.read_text(encoding="utf-8"))
        _daemon(m2h_profile, "stop", commands, "m2h-target-daemon-stop", expect_success=False)

        raw["memos_to_hindsight"] = {
            "logical_resource_id": M2H_LOGICAL_ID,
            "representation_kind": "text/plain; charset=utf-8",
            "content": M2H_CONTENT,
            "source_domain_refs": [DOMAIN],
            "destination_domain_refs": [DOMAIN],
            "provenance_refs": PROVENANCE,
            "source": {
                **m2h_source.get("provider", {}),
                "readback_before": m2h_source.get("readback"),
                "readback_after_target": m2h_source_after.get("readback"),
            },
            "target": {
                "component_id": "hindsight-v0.9.0",
                "component_version": HINDSIGHT_VERSION,
                "native_resource_id": f"hindsight-document:{m2h_bank}/{m2h_doc}",
                "runtime_ref": "hindsight-embed:0.9.0:pg0",
                "readback": m2h_target_text,
            },
            "source_retained": m2h_source_after.get("readback") == M2H_CONTENT,
            "target_readback_matches": m2h_target_text == M2H_CONTENT,
        }
    except Exception as exc:
        raw["execution_error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        # Best effort cleanup of possible running profiles. Data is intentionally
        # not deleted because source-retention is part of the bounded evidence.
        for profile in (
            "agent-memory-exchange-h2m-source",
            "agent-memory-exchange-m2h-target",
        ):
            _daemon(profile, "stop", commands, f"final-stop:{profile}", expect_success=False)
        args.output.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return 0 if "execution_error" not in raw else 1


def _create_profile(profile: str, port: int, database_name: str, commands: list[dict[str, Any]]) -> None:
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
        f"HINDSIGHT_EMBED_API_DATABASE_URL=pg0://{database_name}",
        f"HINDSIGHT_API_DATABASE_URL=pg0://{database_name}",
        "HINDSIGHT_EMBED_API_VERSION=0.9.0",
        "HINDSIGHT_EMBED_CLI_VERSION=0.9.0",
    ]
    command = ["hindsight-embed", "profile", "create", profile, "--port", str(port)]
    for item in env_values:
        command.extend(["--env", item])
    _run(command, commands, f"profile-create:{profile}")


def _daemon(
    profile: str,
    action: str,
    commands: list[dict[str, Any]],
    name: str,
    *,
    expect_success: bool = True,
) -> None:
    _run(["hindsight-embed", "-p", profile, "daemon", action], commands, name, expect_success=expect_success)


def _h_cli_json(profile: str, args: list[str], commands: list[dict[str, Any]], name: str) -> Any:
    result = _run(["hindsight-embed", "-p", profile, "-o", "json", *args], commands, name)
    return _decode_json_prefix(result.stdout, name)


def _decode_json_prefix(stdout: str, name: str) -> Any:
    """Decode the provider JSON value while preserving launcher chatter separately.

    Hindsight Embed v0.9.0 may lazily install its exact CLI on the first
    forwarded command and append installer status text to stdout after the JSON
    response. Raw stdout remains captured in command evidence; qualification
    uses only the first syntactically valid JSON value.
    """
    text = stdout.lstrip()
    try:
        value, _end = json.JSONDecoder().raw_decode(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{name} did not begin with JSON: {stdout[:500]!r}") from exc
    return value


def _memos_endpoint(
    args: argparse.Namespace,
    *,
    action: str,
    home: Path,
    trace_id: str,
    content: str | None,
    output: Path,
    commands: list[dict[str, Any]],
    name: str,
) -> None:
    command = [
        "node",
        "reference/run_memos_local_v2017_exchange_endpoint.mjs",
        "--action",
        action,
        "--package-root",
        str(args.memos_package_root),
        "--home",
        str(home),
        "--trace-id",
        trace_id,
        "--output",
        str(output),
    ]
    if content is not None:
        command.extend(["--content", content])
    _run(command, commands, name)


def _run(
    command: list[str],
    commands: list[dict[str, Any]],
    name: str,
    *,
    expect_success: bool = True,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=300, env=env)
    except Exception as exc:
        commands.append({
            "name": name,
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "exception": f"{type(exc).__name__}: {exc}",
        })
        if expect_success:
            raise
        return subprocess.CompletedProcess(command, 255, "", str(exc))
    commands.append({
        "name": name,
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    })
    if expect_success and result.returncode != 0:
        raise RuntimeError(f"{name} failed with exit {result.returncode}: {result.stderr[-1200:]}")
    return result


def _document_text(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    for key in ("original_text", "text", "content"):
        candidate = value.get(key)
        if isinstance(candidate, str):
            return candidate
    return None


if __name__ == "__main__":
    sys.exit(main())
