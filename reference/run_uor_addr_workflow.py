#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess

from agentmem_ref.uor_content_reference import (
    UorBindingUnavailable,
    UorInvalidInput,
    default_profile_metadata,
    evaluate_json_content_reference,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "uor-addr-v0.2.0-json-vectors.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--rust-probe", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    from uor_addr import AddressError, kappa
    binding_version = importlib.metadata.version("uor-addr")

    def py_address(raw: bytes) -> str:
        try:
            return kappa.json_address(raw)
        except AddressError as exc:
            raise UorInvalidInput(str(exc)) from exc

    def rust_address(raw: bytes) -> str:
        result = subprocess.run([args.rust_probe], input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode:
            raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
        return result.stdout.decode("ascii").strip()

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    labels = {}
    rows = []
    for vector in fixture["vectors"]:
        raw = vector["json_text"].encode("utf-8")
        py_label = py_address(raw)
        rust_label = rust_address(raw)
        evidence = evaluate_json_content_reference(
            raw,
            address_fn=py_address,
            binding_name="uor-addr-python",
            binding_version=binding_version,
            claimed_label=rust_label,
        )
        labels[vector["id"]] = py_label
        rows.append({
            "vector_id": vector["id"],
            "python_label": py_label,
            "rust_label": rust_label,
            "byte_identical": py_label == rust_label,
            "profile_status": evidence["status"],
        })

    mismatch_count = sum(not row["byte_identical"] for row in rows)
    equivalence_failures = sum(labels[a] != labels[b] for a, b in fixture["equivalent_pairs"])
    distinction_failures = sum(labels[a] == labels[b] for a, b in fixture["distinct_pairs"])

    sample = evaluate_json_content_reference(
        fixture["vectors"][0]["json_text"].encode("utf-8"),
        address_fn=py_address,
        binding_name="uor-addr-python",
        binding_version=binding_version,
    )
    label = sample["generated_label"]
    failures = []

    for case, result in [
        ("mismatch", evaluate_json_content_reference(b'{"different":true}', address_fn=py_address, binding_name="uor-addr-python", binding_version=binding_version, claimed_label=label)),
        ("malformed-label", evaluate_json_content_reference(b'{"a":1}', address_fn=py_address, binding_name="uor-addr-python", binding_version=binding_version, claimed_label="sha256:not-valid")),
    ]:
        failures.append({"case": case, "status": result["status"], "fail_open": result["failure"]["fail_open"]})

    metadata = default_profile_metadata()
    metadata["profile_version"] = "999.0.0"
    result = evaluate_json_content_reference(b'{"a":1}', address_fn=py_address, binding_name="uor-addr-python", binding_version=binding_version, profile_metadata=metadata)
    failures.append({"case": "unsupported-profile", "status": result["status"], "fail_open": result["failure"]["fail_open"]})

    metadata = default_profile_metadata()
    metadata["future_field"] = "unknown"
    result = evaluate_json_content_reference(b'{"a":1}', address_fn=py_address, binding_name="uor-addr-python", binding_version=binding_version, profile_metadata=metadata)
    failures.append({"case": "unknown-metadata", "status": result["status"], "fail_open": result["failure"]["fail_open"]})

    def unavailable(_: bytes) -> str:
        raise UorBindingUnavailable("simulated optional binding unavailability")

    result = evaluate_json_content_reference(b'{"a":1}', address_fn=unavailable, binding_name="uor-addr-python", binding_version=binding_version)
    failures.append({"case": "binding-unavailable", "status": result["status"], "fail_open": result["failure"]["fail_open"]})

    result = evaluate_json_content_reference(b'{', address_fn=py_address, binding_name="uor-addr-python", binding_version=binding_version)
    failures.append({"case": "invalid-json", "status": result["status"], "fail_open": result["failure"]["fail_open"]})

    report = {
        "agent_memory_commit": args.agent_memory_commit,
        "external_pin": sample["uor"],
        "binding": {"python": f"uor-addr=={binding_version}", "rust_source": sample["uor"]["source_commit"]},
        "vectors": rows,
        "failure_cases": failures,
        "non_authority": {
            "logical_identity": sample["can_create_logical_memory_identity"],
            "currentness": sample["can_create_lifecycle_currentness"],
            "recall": sample["can_admit_recall"],
            "scope": sample["can_cross_isolation_boundary"],
            "pama": sample["can_satisfy_pama_mutation_authority"],
        },
        "metrics": {
            "vector_count": len(rows),
            "cross_language_mismatches": mismatch_count,
            "canonical_equivalence_failures": equivalence_failures,
            "typed_distinction_failures": distinction_failures,
            "failure_posture_failures": sum(row["fail_open"] is not False for row in failures),
        },
        "license": {"uor": sample["uor"]["license"], "copied_implementation_code": False, "ordinary_runtime_dependency_added": False},
    }
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 1 if any(v for k, v in report["metrics"].items() if k != "vector_count") else 0


if __name__ == "__main__":
    raise SystemExit(main())
