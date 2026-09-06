"""Minimal public HTTPS transport for Agent Memory's DashClaw provider.

This Worker exposes decision projection only. It does not mutate Agent Memory,
persist state, call AGT/AgentTrust/QOR, or use Cloudflare storage/services.
"""

from __future__ import annotations

import hmac
import json
from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint

from agentmem_ref.dashclaw_authority import ProjectScopedAuthorityResolver
from agentmem_ref.dashclaw_external_verdict import (
    DashClawRequestError,
    StaticAuthorityResolver,
    evaluate_request,
)

MAX_BODY_BYTES = 64 * 1024
CONFIG_ENV = "DASHCLAW_PROVIDER_CONFIG"


def _json_response(status: int, payload: dict, *, extra_headers: dict[str, str] | None = None) -> Response:
    headers = {
        "content-type": "application/json; charset=utf-8",
        "cache-control": "no-store",
        "x-content-type-options": "nosniff",
    }
    if extra_headers:
        headers.update(extra_headers)
    return Response(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        status=status,
        headers=headers,
    )


def _load_provider_config(env) -> tuple[str, ProjectScopedAuthorityResolver]:
    raw = getattr(env, CONFIG_ENV, None)
    if not isinstance(raw, str) or not raw:
        raise ValueError("provider config secret missing")

    document = json.loads(raw)
    if not isinstance(document, dict):
        raise ValueError("provider config must be an object")

    token = document.get("bearer_token")
    authority = document.get("authority")
    if not isinstance(token, str) or not token:
        raise ValueError("bearer_token must be a non-empty string")
    if not isinstance(authority, dict):
        raise ValueError("authority must be an object")

    resolver = ProjectScopedAuthorityResolver(StaticAuthorityResolver.from_document(authority))
    return token, resolver


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        path = urlparse(request.url).path
        if path != "/v1/external-verdict":
            return _json_response(404, {"error": "not_found"})

        if request.method != "POST":
            return _json_response(405, {"error": "method_not_allowed"}, extra_headers={"allow": "POST"})

        try:
            token, authority_resolver = _load_provider_config(self.env)
        except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
            # Configuration errors are availability failures, not policy verdicts.
            # Keep details out of the public response and let DashClaw apply the
            # explicitly configured unavailability posture.
            return _json_response(503, {"error": "provider_not_configured"})

        authorization = request.headers.get("authorization")
        expected = f"Bearer {token}"
        if not isinstance(authorization, str) or not hmac.compare_digest(authorization, expected):
            return _json_response(
                401,
                {"error": "unauthorized"},
                extra_headers={"www-authenticate": "Bearer"},
            )

        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > MAX_BODY_BYTES:
                    return _json_response(413, {"error": "body_too_large"})
            except (TypeError, ValueError):
                return _json_response(400, {"error": "invalid_content_length"})

        try:
            body = await request.text()
        except Exception:
            return _json_response(400, {"error": "invalid_body"})

        body_size = len(body.encode("utf-8"))
        if body_size <= 0:
            return _json_response(400, {"error": "empty_body"})
        if body_size > MAX_BODY_BYTES:
            return _json_response(413, {"error": "body_too_large"})

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return _json_response(400, {"error": "invalid_json"})

        if not isinstance(payload, dict):
            return _json_response(400, {"error": "request_must_be_object"})

        try:
            verdict = evaluate_request(payload, authority_resolver)
        except DashClawRequestError:
            # Missing/invalid DashClaw identity cannot be answered with a
            # contract-valid echoed verdict. Non-2xx is the honest result.
            return _json_response(400, {"error": "invalid_dashclaw_request"})

        return _json_response(200, verdict)
