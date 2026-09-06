#!/usr/bin/env python3
"""Minimal stdlib HTTP entrypoint for the DashClaw external-verdict adapter.

This is a reference/integration server, not a production deployment shape.
DashClaw requires a public HTTPS provider URL, so use this behind a controlled
HTTPS reverse proxy/tunnel for live interoperability testing.

Mutation authority is never inferred from DashClaw identity alone. A reference
static grant document may be supplied for integration testing; without one,
mutation requests reach PAMA with unresolved actor authority and deny. The
current #279 endpoint is deliberately project-scoped, so organization identity
cannot be interpreted as organization-wide memory mutation authority. The
connection-test path remains independent and side-effect free.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from agentmem_ref.dashclaw_authority import ProjectScopedAuthorityResolver
from agentmem_ref.dashclaw_external_verdict import (
    DashClawRequestError,
    StaticAuthorityResolver,
    evaluate_request,
)

MAX_BODY_BYTES = 64 * 1024


class ProviderHandler(BaseHTTPRequestHandler):
    bearer_token: str | None = None
    authority_resolver: ProjectScopedAuthorityResolver | None = None

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        # Avoid logging request payloads or bearer tokens in the reference path.
        return

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in ("/", "/v1/external-verdict"):
            self._json(404, {"error": "not_found"})
            return

        if self.bearer_token is not None:
            expected = f"Bearer {self.bearer_token}"
            if self.headers.get("authorization") != expected:
                self._json(401, {"error": "unauthorized"})
                return

        try:
            content_length = int(self.headers.get("content-length", "0"))
        except ValueError:
            self._json(400, {"error": "invalid_content_length"})
            return

        if content_length <= 0 or content_length > MAX_BODY_BYTES:
            self._json(413 if content_length > MAX_BODY_BYTES else 400, {"error": "invalid_body_size"})
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"error": "invalid_json"})
            return

        if not isinstance(payload, dict):
            self._json(400, {"error": "request_must_be_object"})
            return

        try:
            response = evaluate_request(payload, self.authority_resolver)
        except DashClawRequestError as exc:
            # Missing identity cannot be answered with a contract-valid echoed
            # verdict. Non-2xx is therefore the honest conservative result;
            # DashClaw applies the configured unavailability posture.
            self._json(400, {"error": "invalid_dashclaw_request", "detail": str(exc)})
            return

        self._json(200, response)


def _load_token(path: str | None) -> str | None:
    if path is None:
        return None
    value = Path(path).read_text(encoding="utf-8").strip()
    if not value:
        raise SystemExit("bearer token file is empty")
    return value


def _load_authority_resolver(path: str | None) -> ProjectScopedAuthorityResolver | None:
    if path is None:
        return None
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot load authority grants: {exc}") from exc
    if not isinstance(document, dict):
        raise SystemExit("authority grants document must be a JSON object")
    try:
        return ProjectScopedAuthorityResolver(StaticAuthorityResolver.from_document(document))
    except ValueError as exc:
        raise SystemExit(f"invalid authority grants: {exc}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Agent Memory DashClaw v1 external-verdict adapter")
    parser.add_argument("--bind", default="127.0.0.1", help="local bind address; default 127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument(
        "--bearer-token-file",
        help="optional UTF-8 file containing the exact bearer token DashClaw sends",
    )
    parser.add_argument(
        "--authority-grants-file",
        help=(
            "reference-only JSON grants binding org_id + agent_id to exact project/isolation domains; "
            "without this file mutation authority remains unresolved and PAMA denies"
        ),
    )
    args = parser.parse_args()

    ProviderHandler.bearer_token = _load_token(args.bearer_token_file)
    ProviderHandler.authority_resolver = _load_authority_resolver(args.authority_grants_file)
    server = ThreadingHTTPServer((args.bind, args.port), ProviderHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
