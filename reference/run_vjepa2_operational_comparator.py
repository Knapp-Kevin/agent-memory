#!/usr/bin/env python
"""Run the pinned V-JEPA 2.1 frozen-representation comparator for issue #230.

The official encoder weights remain frozen. A small ridge readout is fitted on
exactly the same generated training clips/targets used by the local benchmark.
This is a workload-scoped representation test, not a reproduction of Meta's
published V-JEPA benchmarks or action-conditioned planner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

from agentmem_ref.operational_memory_benchmark import (
    BENCHMARK_VERSION,
    FRAMES,
    SIZE,
    benchmark_external_features,
    make_dataset,
)

VJEPA_SOURCE_COMMIT = "45d025f636dfc58fc2426905fc4a1ab755b1c3e5"
VJEPA_MODEL = "vjepa2_1_vit_base_384"
VJEPA_CHECKPOINT_URL = "https://dl.fbaipublicfiles.com/vjepa2/vjepa2_1_vitb_dist_vitG_384.pt"
FIXTURE_IMAGE_SIZE = SIZE
FIXTURE_FRAMES = FRAMES
BATCH_SIZE = 8


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _clean_key(key: str) -> str:
    for prefix in ("module.", "backbone.", "encoder."):
        if key.startswith(prefix):
            key = key[len(prefix) :]
    return key


def _load_encoder(vjepa_source: Path, checkpoint_path: Path):
    sys.path.insert(0, str(vjepa_source))
    from app.vjepa_2_1.models import vision_transformer  # type: ignore

    model = vision_transformer.vit_base(
        img_size=(FIXTURE_IMAGE_SIZE, FIXTURE_IMAGE_SIZE),
        num_frames=FIXTURE_FRAMES,
        tubelet_size=2,
        uniform_power=False,
        use_sdpa=True,
        use_silu=False,
        use_rope=True,
        use_activation_checkpointing=False,
        img_temporal_dim_size=1,
        interpolate_rope=True,
    )
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if "ema_encoder" not in checkpoint:
        raise RuntimeError("official V-JEPA 2.1 checkpoint lacks ema_encoder")
    state = {_clean_key(key): value for key, value in checkpoint["ema_encoder"].items()}

    # Meta's pinned V-JEPA 2.1 hub loader uses strict=True for this encoder.
    # Preserve that boundary and adapt only the benchmark input geometry.
    load_result = model.load_state_dict(state, strict=True)
    missing = sorted(load_result.missing_keys)
    unexpected = sorted(load_result.unexpected_keys)
    if missing or unexpected:
        raise RuntimeError(
            "strict V-JEPA checkpoint load returned incompatible state: "
            f"missing={missing!r}, unexpected={unexpected!r}"
        )
    model.eval()
    return model, {
        "missing_model_keys": missing,
        "ignored_checkpoint_keys": unexpected,
        "adaptation": "fixture_geometry_only_with_strict_upstream_state",
    }


def _normalize(videos: np.ndarray) -> torch.Tensor:
    # Official transforms use ImageNet mean/std. Input here is 0..255 uint8.
    x = torch.from_numpy(videos).permute(0, 4, 1, 2, 3).to(torch.float32) / 255.0
    mean = torch.tensor([0.485, 0.456, 0.406], dtype=torch.float32).view(1, 3, 1, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225], dtype=torch.float32).view(1, 3, 1, 1, 1)
    return (x - mean) / std


def _features(model, videos: np.ndarray) -> tuple[np.ndarray, float]:
    tensor = _normalize(videos)
    outputs: list[np.ndarray] = []
    start = time.perf_counter()
    with torch.inference_mode():
        for offset in range(0, len(tensor), BATCH_SIZE):
            batch = tensor[offset : offset + BATCH_SIZE]
            tokens = model(batch)
            if not torch.is_tensor(tokens) or tokens.ndim != 3:
                raise RuntimeError(f"unexpected V-JEPA encoder output shape/type: {type(tokens)}")
            pooled = tokens.mean(dim=1)
            outputs.append(pooled.cpu().numpy().astype(np.float32))
    elapsed = time.perf_counter() - start
    return np.concatenate(outputs, axis=0), elapsed


def run(
    *,
    agent_memory_commit: str,
    vjepa_source: Path,
    checkpoint_path: Path,
    expected_checkpoint_sha256: str | None,
) -> dict:
    checkpoint_sha256 = _sha256(checkpoint_path)
    print(f"VJEPA_CHECKPOINT_SHA256={checkpoint_sha256}")
    if expected_checkpoint_sha256 and checkpoint_sha256 != expected_checkpoint_sha256:
        raise RuntimeError(
            f"checkpoint sha256 mismatch: expected {expected_checkpoint_sha256}, got {checkpoint_sha256}"
        )

    dataset = make_dataset()
    model_start = time.perf_counter()
    model, checkpoint_adaptation = _load_encoder(vjepa_source, checkpoint_path)
    model_load_seconds = time.perf_counter() - model_start

    train_features, train_feature_seconds = _features(model, dataset.train_videos)
    test_features, test_feature_seconds = _features(model, dataset.test_videos)
    benchmark = benchmark_external_features(
        name="vjepa2_1_frozen_representation",
        train_features=train_features,
        test_features=test_features,
        dataset=dataset,
    )

    return {
        "comparator_id": "vjepa2-1-frozen-operational-memory",
        "benchmark_version": BENCHMARK_VERSION,
        "agent_memory_commit": agent_memory_commit,
        "passed": True,
        "peer": {
            "repository": "facebookresearch/vjepa2",
            "source_commit": VJEPA_SOURCE_COMMIT,
            "model": VJEPA_MODEL,
            "checkpoint_url": VJEPA_CHECKPOINT_URL,
            "checkpoint_sha256": checkpoint_sha256,
            "checkpoint_key": "ema_encoder",
            "source_license": "MIT",
        },
        "fixture_adaptation": {
            "checkpoint_published_geometry": "384px V-JEPA 2.1 base checkpoint",
            "executed_image_size": FIXTURE_IMAGE_SIZE,
            "executed_frames": FIXTURE_FRAMES,
            "tubelet_size": 2,
            "frozen_encoder": True,
            "readout": "same standardized ridge family as local learned baseline",
            "checkpoint_state_adaptation": checkpoint_adaptation,
            "published_benchmark_reproduction": False,
            "action_conditioned_planning_tested": False,
        },
        "representation_result": benchmark,
        "runtime": {
            "model_load_seconds": round(model_load_seconds, 6),
            "train_feature_seconds": round(train_feature_seconds, 6),
            "test_feature_seconds": round(test_feature_seconds, 6),
            "torch_version": torch.__version__,
            "device": "cpu",
        },
        "governance_posture": {
            "pretrained_source_provenance": "external_checkpoint_and_source_commit",
            "local_readout_provenance": "benchmark_training_set_manifest",
            "per_output_source_provenance": "not_established",
            "local_exact_delete_or_correction_without_refit": False,
            "encoder_retrain_required_for_local_label_correction": False,
            "readout_refit_required_for_changed_training_evidence": True,
            "checkpoint_content_deletion_proof": "not_established",
        },
        "interpretation": {
            "representation_quality_is_not_authority": True,
            "pretrained_checkpoint_is_not_canonical_agent_memory": True,
            "stale_readout_evidence_requires_rebuild": True,
            "result_is_workload_scoped": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--vjepa-source", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--expected-checkpoint-sha256")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run(
        agent_memory_commit=args.agent_memory_commit,
        vjepa_source=Path(args.vjepa_source),
        checkpoint_path=Path(args.checkpoint),
        expected_checkpoint_sha256=args.expected_checkpoint_sha256,
    )
    result = report["representation_result"]
    for phase in ("current_only", "stale_contaminated", "recovered_current_only"):
        if result[phase]["all"]["count"] <= 0:
            raise SystemExit(f"V-JEPA comparator produced no rows for {phase}")
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
