"""Executable provider-unavailability probe for component qualification.

The probe records the operating-system/runtime failure produced by invoking the
configured provider path. It does not synthesize an outage record from a flag.
A qualification workflow can deliberately make a provider path unavailable,
invoke this probe, preserve the raw failure, and then evaluate explicit fallback
without relabeling failure as success.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Sequence

from .component_fallback import ProviderFailure
from .qualification import AdapterResult, QualificationSubject


class ProviderProbeError(RuntimeError):
    """The expected provider-unavailable condition was not reproduced."""


@dataclass(frozen=True)
class ProviderUnavailableProbe:
    failure: ProviderFailure
    adapter_result: AdapterResult
    raw_path: Path
    normalized_path: Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def probe_missing_executable(
    *,
    subject: QualificationSubject,
    executable: Path,
    args: Sequence[str],
    raw_path: Path,
    normalized_path: Path,
    trace_ref: str,
    timeout_seconds: float = 10.0,
) -> ProviderUnavailableProbe:
    """Invoke an expected-missing executable and preserve the real OS result.

    The probe succeeds only when the configured executable is actually missing.
    An executable that runs, exits non-zero for another reason, or times out is a
    different failure mode and must receive its own evidence profile rather than
    being laundered into ``provider_unavailable``.
    """

    argv = [str(executable), *args]
    try:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as exc:
        raw = {
            "probe": "missing_executable",
            "argv": argv,
            "exception_type": type(exc).__name__,
            "errno": exc.errno,
            "strerror": exc.strerror,
            "filename": exc.filename,
        }
        _write_json(raw_path, raw)
        normalized = {
            "component_id": subject.component_id,
            "capability_id": subject.capability_id,
            "failure_result": "provider_unavailable",
            "currentness": "unavailable",
            "runtime_identity": str(executable),
            "raw_evidence_ref": str(raw_path),
            "trace_ref": trace_ref,
            "authority_effect": "none",
        }
        _write_json(normalized_path, normalized)
        failure = ProviderFailure(
            component_id=subject.component_id,
            capability_id=subject.capability_id,
            failure_result="provider_unavailable",
            evidence_ref=str(raw_path),
            trace_ref=trace_ref,
        )
        result = AdapterResult(
            subject=subject,
            operation="provider_availability_probe",
            runtime_identity=str(executable),
            input_refs=(f"executable:{executable}",),
            raw_provider_refs=(str(raw_path),),
            normalized_refs=(str(normalized_path),),
            currentness="unavailable",
            failure_result="provider_unavailable",
            trace_ref=trace_ref,
        )
        return ProviderUnavailableProbe(
            failure=failure,
            adapter_result=result,
            raw_path=raw_path,
            normalized_path=normalized_path,
        )
    except subprocess.TimeoutExpired as exc:
        raise ProviderProbeError(
            f"provider invocation timed out instead of reproducing missing-executable unavailability: {exc}"
        ) from exc

    raise ProviderProbeError(
        "expected provider executable to be unavailable, but it executed "
        f"with return code {completed.returncode}"
    )
