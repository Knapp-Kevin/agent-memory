#!/usr/bin/env python3
"""Run the pinned OpenSSL RFC 3161 verification comparator for #265.

The comparator can either use an explicitly supplied OpenSSL binary/fixture
set or provision the exact official OpenSSL 3.6.3 release asset after verifying
its published SHA-256 digest. The result is external time evidence only; it does
not establish event occurrence, Agent Memory currentness, or PAMA authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path

OPENSSL_VERSION = "3.6.3"
OPENSSL_COMMIT = "aae016bfd52fcad2bc9657c2c782cfdf73b1ed5f"
OPENSSL_RELEASE_URL = "https://github.com/openssl/openssl/releases/download/openssl-3.6.3/openssl-3.6.3.tar.gz"
OPENSSL_RELEASE_SHA256 = "243a86649cf6f23eeb6a2ff2456e09e5d77dd9018a54d3d96b0c6bdd6ba6c7f1"
FIXTURE_SOURCE = "openssl/openssl:test/recipes/80-test_tsa_data"
AUTHORITY_EFFECT = "none"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def provision_release(workdir: Path) -> tuple[Path, Path, str]:
    workdir.mkdir(parents=True, exist_ok=True)
    archive = workdir / f"openssl-{OPENSSL_VERSION}.tar.gz"
    urllib.request.urlretrieve(OPENSSL_RELEASE_URL, archive)
    archive_digest = sha256_file(archive)
    expected = "sha256:" + OPENSSL_RELEASE_SHA256
    if archive_digest != expected:
        raise SystemExit(f"OpenSSL release digest mismatch: {archive_digest} != {expected}")

    with tarfile.open(archive, "r:gz") as bundle:
        bundle.extractall(workdir, filter="data")

    source = workdir / f"openssl-{OPENSSL_VERSION}"
    configured = run(["./Configure", "no-shared", "no-tests"], cwd=source)
    if configured.returncode != 0:
        raise SystemExit(f"OpenSSL configure failed: {configured.stderr[-4000:]}")
    built = run(["make", "-j2", "build_sw"], cwd=source)
    if built.returncode != 0:
        raise SystemExit(f"OpenSSL build failed: {built.stderr[-4000:]}")

    return source / "apps" / "openssl", source / "test" / "recipes" / "80-test_tsa_data", archive_digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--openssl-bin")
    parser.add_argument("--fixture-dir")
    parser.add_argument("--provision-release", action="store_true")
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    release_digest: str | None = None
    if args.provision_release:
        with tempfile.TemporaryDirectory(prefix="agent-memory-openssl-") as temp_dir:
            openssl_path, fixture_path, release_digest = provision_release(Path(temp_dir))
            return execute_comparator(
                openssl_path,
                fixture_path,
                agent_memory_commit=args.agent_memory_commit,
                output=Path(args.output),
                release_digest=release_digest,
            )

    if not args.openssl_bin or not args.fixture_dir:
        parser.error("provide --provision-release or both --openssl-bin and --fixture-dir")
    return execute_comparator(
        Path(args.openssl_bin).resolve(),
        Path(args.fixture_dir).resolve(),
        agent_memory_commit=args.agent_memory_commit,
        output=Path(args.output),
        release_digest=release_digest,
    )


def execute_comparator(
    openssl_path: Path,
    fixtures: Path,
    *,
    agent_memory_commit: str,
    output: Path,
    release_digest: str | None,
) -> int:
    openssl = str(openssl_path)
    query = fixtures / "all-zero.tsq"
    response = fixtures / "sectigo-all-zero.tsr"
    trusted_root = fixtures / "user-trust-ca.pem"
    alternate_root = fixtures / "comodo-aaa.pem"

    for path in (query, response, trusted_root, alternate_root):
        if not path.is_file():
            raise SystemExit(f"missing comparator fixture: {path}")

    version = run([openssl, "version"])
    if version.returncode != 0 or f"OpenSSL {OPENSSL_VERSION}" not in version.stdout:
        raise SystemExit(f"unexpected OpenSSL version: {version.stdout.strip()} {version.stderr.strip()}")

    valid = run([
        openssl, "ts", "-verify", "-no_check_time", "-queryfile", str(query),
        "-in", str(response), "-CAfile", str(trusted_root),
    ])
    wrong_root = run([
        openssl, "ts", "-verify", "-no_check_time", "-queryfile", str(query),
        "-in", str(response), "-CAfile", str(alternate_root),
    ])
    inspected = run([openssl, "ts", "-reply", "-in", str(response), "-text"])

    result = {
        "schema_version": "1.0.0",
        "comparator": "openssl-rfc3161",
        "agent_memory_commit": agent_memory_commit,
        "external_source": {
            "repository": "openssl/openssl",
            "version": OPENSSL_VERSION,
            "commit": OPENSSL_COMMIT,
            "release_asset_sha256": "sha256:" + OPENSSL_RELEASE_SHA256,
            "provisioned_release_digest": release_digest,
            "fixture_source": FIXTURE_SOURCE,
        },
        "fixture_digests": {
            "query": sha256_file(query),
            "response": sha256_file(response),
            "trusted_root": sha256_file(trusted_root),
            "alternate_root": sha256_file(alternate_root),
        },
        "checks": {
            "trusted_root_verifies": valid.returncode == 0,
            "wrong_root_rejected": wrong_root.returncode != 0,
            "response_inspectable": inspected.returncode == 0,
            "release_digest_verified": release_digest in {None, "sha256:" + OPENSSL_RELEASE_SHA256},
        },
        "verification": {
            "status": "verified" if valid.returncode == 0 else "invalid",
            "claim_kind": "existence_by_time",
            "trust_chain_verified": valid.returncode == 0,
            "wrong_trust_root_rejected": wrong_root.returncode != 0,
            "event_occurrence_time_proven": False,
            "currentness": "not_established",
            "authority_effect": AUTHORITY_EFFECT,
        },
    }

    result["status"] = "pass" if all(result["checks"].values()) else "fail"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
