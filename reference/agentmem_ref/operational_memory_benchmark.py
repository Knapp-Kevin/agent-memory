"""Matched operational-memory capability benchmark for issue #230.

The benchmark is intentionally small and deterministic. It compares multiple
representations on the same generated visual-dynamics stream and reports stale
evidence contamination separately from prediction quality.

NumPy is an isolated benchmark dependency; it is not part of Agent Memory's core
reference requirements.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

BENCHMARK_VERSION = "1.0.0"
SEED = 2302026
FRAMES = 4
SIZE = 64
TARGET_RADIUS = 3
INTERCEPT_RADIUS = 5.0
TRAIN_PER_PROFILE = 24
TEST_PER_PROFILE = 12
PCA_DIM = 16
RIDGE_ALPHA = 1e-2

DIRECTIONS = np.array(
    [
        [-3.0, 0.0],
        [3.0, 0.0],
        [0.0, -3.0],
        [0.0, 3.0],
        [-2.0, -2.0],
        [-2.0, 2.0],
        [2.0, -2.0],
        [2.0, 2.0],
    ],
    dtype=np.float32,
)


@dataclass(frozen=True)
class Dataset:
    train_videos: np.ndarray
    train_targets: np.ndarray
    train_ids: tuple[str, ...]
    train_profiles: tuple[str, ...]
    test_videos: np.ndarray
    test_targets: np.ndarray
    test_ids: tuple[str, ...]
    test_profiles: tuple[str, ...]


def _sample_id(split: str, profile: str, index: int) -> str:
    return f"visual-dynamics:{BENCHMARK_VERSION}:{split}:{profile}:{index:03d}"


def _draw_square(frame: np.ndarray, x: float, y: float, color: tuple[int, int, int], radius: int) -> None:
    cx = int(round(x))
    cy = int(round(y))
    x0, x1 = max(0, cx - radius), min(frame.shape[1], cx + radius + 1)
    y0, y1 = max(0, cy - radius), min(frame.shape[0], cy + radius + 1)
    frame[y0:y1, x0:x1, :] = np.asarray(color, dtype=np.uint8)


def _make_video(rng: np.random.Generator, profile: str, sample_index: int) -> tuple[np.ndarray, np.ndarray]:
    direction = DIRECTIONS[int(rng.integers(0, len(DIRECTIONS)))]
    margin = 15
    x = float(rng.integers(margin, SIZE - margin))
    y = float(rng.integers(margin, SIZE - margin))

    video = np.zeros((FRAMES, SIZE, SIZE, 3), dtype=np.uint8)
    # A low-amplitude background gradient prevents a completely trivial black canvas
    # without leaking the target label.
    gx = np.linspace(8, 28, SIZE, dtype=np.float32)
    gy = np.linspace(0, 12, SIZE, dtype=np.float32)[:, None]
    base = np.clip(gx + gy, 0, 255).astype(np.uint8)

    for t in range(FRAMES):
        frame = video[t]
        frame[..., 0] = base
        frame[..., 1] = np.flip(base, axis=1)
        frame[..., 2] = 12

        px = x + direction[0] * t
        py = y + direction[1] * t
        _draw_square(frame, px, py, (240, 38, 32), TARGET_RADIUS)

        if profile == "degraded":
            # Deterministic per-sample nuisance structure: distractors, noise, and
            # occasional target occlusion. These are observations, not hidden labels.
            for _ in range(2):
                dx = float(rng.integers(8, SIZE - 8))
                dy = float(rng.integers(8, SIZE - 8))
                color = (40, int(rng.integers(120, 240)), int(rng.integers(80, 210)))
                _draw_square(frame, dx, dy, color, int(rng.integers(2, 5)))
            noise = rng.normal(0.0, 18.0, size=frame.shape)
            frame[:] = np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)
            if sample_index % 4 == 0 and t == FRAMES - 1:
                # Occlude the latest target observation in one quarter of degraded clips.
                ox0 = max(0, int(round(px)) - TARGET_RADIUS - 2)
                ox1 = min(SIZE, int(round(px)) + TARGET_RADIUS + 3)
                oy0 = max(0, int(round(py)) - TARGET_RADIUS - 2)
                oy1 = min(SIZE, int(round(py)) + TARGET_RADIUS + 3)
                frame[oy0:oy1, ox0:ox1, :] = 22

    target = np.array([x + direction[0] * FRAMES, y + direction[1] * FRAMES], dtype=np.float32)
    return video, target


def make_dataset(seed: int = SEED) -> Dataset:
    rng = np.random.default_rng(seed)
    train_videos: list[np.ndarray] = []
    train_targets: list[np.ndarray] = []
    train_ids: list[str] = []
    train_profiles: list[str] = []
    test_videos: list[np.ndarray] = []
    test_targets: list[np.ndarray] = []
    test_ids: list[str] = []
    test_profiles: list[str] = []

    for profile in ("clean", "degraded"):
        for index in range(TRAIN_PER_PROFILE):
            video, target = _make_video(rng, profile, index)
            train_videos.append(video)
            train_targets.append(target)
            train_ids.append(_sample_id("train", profile, index))
            train_profiles.append(profile)
        for index in range(TEST_PER_PROFILE):
            video, target = _make_video(rng, profile, 1000 + index)
            test_videos.append(video)
            test_targets.append(target)
            test_ids.append(_sample_id("test", profile, index))
            test_profiles.append(profile)

    return Dataset(
        train_videos=np.stack(train_videos),
        train_targets=np.stack(train_targets),
        train_ids=tuple(train_ids),
        train_profiles=tuple(train_profiles),
        test_videos=np.stack(test_videos),
        test_targets=np.stack(test_targets),
        test_ids=tuple(test_ids),
        test_profiles=tuple(test_profiles),
    )


def pooled_clip_descriptor(videos: np.ndarray, pool: int = 8) -> np.ndarray:
    if videos.ndim != 5 or videos.shape[1:4] != (FRAMES, SIZE, SIZE):
        raise ValueError("unexpected video batch shape")
    if SIZE % pool:
        raise ValueError("pool must divide SIZE")
    x = videos.astype(np.float32) / 255.0
    n, t, h, w, c = x.shape
    x = x.reshape(n, t, h // pool, pool, w // pool, pool, c).mean(axis=(3, 5))
    return x.reshape(n, -1)


def explicit_features(videos: np.ndarray) -> np.ndarray:
    rows: list[list[float]] = []
    for video in videos:
        row: list[float] = []
        for frame in video:
            pixels = frame.astype(np.int16)
            mask = (
                (pixels[..., 0] > 150)
                & (pixels[..., 0] - pixels[..., 1] > 55)
                & (pixels[..., 0] - pixels[..., 2] > 55)
            )
            ys, xs = np.nonzero(mask)
            if len(xs):
                row.extend([float(xs.mean()) / SIZE, float(ys.mean()) / SIZE, 1.0])
            else:
                row.extend([0.0, 0.0, 0.0])
        rows.append(row)
    return np.asarray(rows, dtype=np.float32)


def explicit_predict(videos: np.ndarray) -> np.ndarray:
    features = explicit_features(videos).reshape(len(videos), FRAMES, 3)
    predictions: list[np.ndarray] = []
    for row in features:
        observations = [
            np.array([obs[0] * SIZE, obs[1] * SIZE], dtype=np.float32)
            for obs in row
            if obs[2] > 0.5
        ]
        if len(observations) >= 2:
            velocity = observations[-1] - observations[-2]
            prediction = observations[-1] + velocity
        elif observations:
            prediction = observations[-1]
        else:
            prediction = np.array([SIZE / 2, SIZE / 2], dtype=np.float32)
        predictions.append(prediction)
    return np.stack(predictions)


def fit_standardized_ridge(features: np.ndarray, targets: np.ndarray, alpha: float = RIDGE_ALPHA) -> dict[str, np.ndarray]:
    x = np.asarray(features, dtype=np.float64)
    y = np.asarray(targets, dtype=np.float64)
    mean = x.mean(axis=0)
    std = x.std(axis=0)
    std[std < 1e-8] = 1.0
    z = (x - mean) / std
    z = np.concatenate([z, np.ones((len(z), 1), dtype=np.float64)], axis=1)
    penalty = np.eye(z.shape[1], dtype=np.float64) * alpha
    penalty[-1, -1] = 0.0
    weights = np.linalg.solve(z.T @ z + penalty, z.T @ y)
    return {"mean": mean, "std": std, "weights": weights}


def predict_ridge(model: dict[str, np.ndarray], features: np.ndarray) -> np.ndarray:
    x = np.asarray(features, dtype=np.float64)
    z = (x - model["mean"]) / model["std"]
    z = np.concatenate([z, np.ones((len(z), 1), dtype=np.float64)], axis=1)
    return (z @ model["weights"]).astype(np.float32)


def fit_pca(train_features: np.ndarray, dimensions: int = PCA_DIM) -> dict[str, np.ndarray]:
    x = np.asarray(train_features, dtype=np.float64)
    mean = x.mean(axis=0)
    centered = x - mean
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    dims = min(dimensions, vh.shape[0], vh.shape[1])
    return {"mean": mean, "components": vh[:dims].T}


def transform_pca(model: dict[str, np.ndarray], features: np.ndarray) -> np.ndarray:
    x = np.asarray(features, dtype=np.float64)
    return ((x - model["mean"]) @ model["components"]).astype(np.float32)


def nearest_neighbor_predict(train_features: np.ndarray, train_targets: np.ndarray, test_features: np.ndarray) -> np.ndarray:
    train = np.asarray(train_features, dtype=np.float32)
    test = np.asarray(test_features, dtype=np.float32)
    predictions = []
    for row in test:
        distance = ((train - row) ** 2).mean(axis=1)
        predictions.append(train_targets[int(np.argmin(distance))])
    return np.asarray(predictions, dtype=np.float32)


def make_stale_training(features: np.ndarray, targets: np.ndarray, *, count: int = 12) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    count = min(count, len(features))
    stale_features = np.asarray(features[:count]).copy()
    stale_targets = np.asarray(targets[:count]).copy()
    # Conflicting historical label: mirror the one-step displacement around the
    # center. It is intentionally wrong current evidence, not random noise.
    stale_targets = np.clip((SIZE - 1) - stale_targets, 0, SIZE - 1)
    # Put stale rows first so exact nearest-neighbor ties expose contamination.
    combined_features = np.concatenate([stale_features, features], axis=0)
    combined_targets = np.concatenate([stale_targets, targets], axis=0)
    stale_mask = np.concatenate([np.ones(count, dtype=bool), np.zeros(len(features), dtype=bool)])
    return combined_features, combined_targets, stale_mask


def metric_block(predictions: np.ndarray, targets: np.ndarray, profiles: tuple[str, ...]) -> dict[str, Any]:
    pred = np.asarray(predictions, dtype=np.float32)
    target = np.asarray(targets, dtype=np.float32)
    euclidean = np.linalg.norm(pred - target, axis=1)
    absolute = np.abs(pred - target).mean(axis=1)

    def _one(mask: np.ndarray) -> dict[str, float]:
        return {
            "mean_absolute_error_px": round(float(absolute[mask].mean()), 6),
            "mean_euclidean_error_px": round(float(euclidean[mask].mean()), 6),
            "intercept_success_rate": round(float((euclidean[mask] <= INTERCEPT_RADIUS).mean()), 6),
            "count": int(mask.sum()),
        }

    profile_array = np.asarray(profiles)
    result = {"all": _one(np.ones(len(pred), dtype=bool))}
    for profile in ("clean", "degraded"):
        result[profile] = _one(profile_array == profile)
    return result


def _benchmark_learned(
    name: str,
    train_features: np.ndarray,
    test_features: np.ndarray,
    dataset: Dataset,
) -> dict[str, Any]:
    fit_start = time.perf_counter()
    current_model = fit_standardized_ridge(train_features, dataset.train_targets)
    fit_seconds = time.perf_counter() - fit_start
    infer_start = time.perf_counter()
    current_predictions = predict_ridge(current_model, test_features)
    infer_seconds = time.perf_counter() - infer_start

    stale_x, stale_y, _ = make_stale_training(train_features, dataset.train_targets)
    stale_model = fit_standardized_ridge(stale_x, stale_y)
    stale_predictions = predict_ridge(stale_model, test_features)

    current_metrics = metric_block(current_predictions, dataset.test_targets, dataset.test_profiles)
    stale_metrics = metric_block(stale_predictions, dataset.test_targets, dataset.test_profiles)
    return {
        "representation": name,
        "current_only": current_metrics,
        "stale_contaminated": stale_metrics,
        "recovered_current_only": current_metrics,
        "stale_influence_delta_mae_px": round(
            stale_metrics["all"]["mean_absolute_error_px"] - current_metrics["all"]["mean_absolute_error_px"],
            6,
        ),
        "feature_dimension": int(train_features.shape[1]),
        "train_rows_current": int(len(train_features)),
        "train_rows_contaminated": int(len(stale_x)),
        "fit_seconds": round(fit_seconds, 6),
        "inference_seconds": round(infer_seconds, 6),
    }


def benchmark_external_features(
    *,
    name: str,
    train_features: np.ndarray,
    test_features: np.ndarray,
    dataset: Dataset | None = None,
) -> dict[str, Any]:
    data = dataset or make_dataset()
    if len(train_features) != len(data.train_targets) or len(test_features) != len(data.test_targets):
        raise ValueError("external feature rows must match the shared benchmark dataset")
    return _benchmark_learned(name, train_features, test_features, data)


def run_operational_memory_benchmark() -> dict[str, Any]:
    dataset = make_dataset()
    train_descriptor = pooled_clip_descriptor(dataset.train_videos)
    test_descriptor = pooled_clip_descriptor(dataset.test_videos)

    # A. Explicit extracted current observation state.
    start = time.perf_counter()
    explicit_predictions = explicit_predict(dataset.test_videos)
    explicit_seconds = time.perf_counter() - start
    explicit_metrics = metric_block(explicit_predictions, dataset.test_targets, dataset.test_profiles)
    explicit = {
        "representation": "explicit_extracted",
        "current_only": explicit_metrics,
        "stale_contaminated": explicit_metrics,
        "recovered_current_only": explicit_metrics,
        "stale_influence_delta_mae_px": 0.0,
        "feature_dimension": int(explicit_features(dataset.test_videos).shape[1]),
        "train_rows_current": 0,
        "train_rows_contaminated": 0,
        "fit_seconds": 0.0,
        "inference_seconds": round(explicit_seconds, 6),
    }

    # B. Retrieval memory.
    retrieval_start = time.perf_counter()
    retrieval_predictions = nearest_neighbor_predict(train_descriptor, dataset.train_targets, test_descriptor)
    retrieval_seconds = time.perf_counter() - retrieval_start
    stale_descriptor, stale_targets, _ = make_stale_training(train_descriptor, dataset.train_targets)
    stale_retrieval = nearest_neighbor_predict(stale_descriptor, stale_targets, test_descriptor)
    retrieval_current = metric_block(retrieval_predictions, dataset.test_targets, dataset.test_profiles)
    retrieval_stale = metric_block(stale_retrieval, dataset.test_targets, dataset.test_profiles)
    retrieval = {
        "representation": "retrieval_nearest_exemplar",
        "current_only": retrieval_current,
        "stale_contaminated": retrieval_stale,
        "recovered_current_only": retrieval_current,
        "stale_influence_delta_mae_px": round(
            retrieval_stale["all"]["mean_absolute_error_px"] - retrieval_current["all"]["mean_absolute_error_px"], 6
        ),
        "feature_dimension": int(train_descriptor.shape[1]),
        "train_rows_current": int(len(train_descriptor)),
        "train_rows_contaminated": int(len(stale_descriptor)),
        "fit_seconds": 0.0,
        "inference_seconds": round(retrieval_seconds, 6),
    }

    # C. Compact learned predictive state.
    pca_fit_start = time.perf_counter()
    pca = fit_pca(train_descriptor)
    pca_fit_seconds = time.perf_counter() - pca_fit_start
    train_latent = transform_pca(pca, train_descriptor)
    test_latent = transform_pca(pca, test_descriptor)
    latent = _benchmark_learned("compact_learned_predictive", train_latent, test_latent, dataset)
    latent["representation_fit_seconds"] = round(pca_fit_seconds, 6)

    # D. Hybrid explicit + learned representation.
    train_explicit = explicit_features(dataset.train_videos)
    test_explicit = explicit_features(dataset.test_videos)
    hybrid_train = np.concatenate([train_explicit, train_latent], axis=1)
    hybrid_test = np.concatenate([test_explicit, test_latent], axis=1)
    hybrid = _benchmark_learned("hybrid_explicit_plus_learned", hybrid_train, hybrid_test, dataset)
    hybrid["representation_fit_seconds"] = round(pca_fit_seconds, 6)

    dataset_manifest = {
        "benchmark_version": BENCHMARK_VERSION,
        "seed": SEED,
        "frames": FRAMES,
        "size": SIZE,
        "train_ids": list(dataset.train_ids),
        "test_ids": list(dataset.test_ids),
        "train_profiles": list(dataset.train_profiles),
        "test_profiles": list(dataset.test_profiles),
    }
    manifest_digest = "sha256:" + hashlib.sha256(
        json.dumps(dataset_manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return {
        "benchmark_id": "matched-operational-memory-visual-dynamics",
        "benchmark_version": BENCHMARK_VERSION,
        "dataset_manifest_digest": manifest_digest,
        "dataset": {
            "seed": SEED,
            "train_rows": len(dataset.train_ids),
            "test_rows": len(dataset.test_ids),
            "profiles": ["clean", "degraded"],
            "frames": FRAMES,
            "frame_size": [SIZE, SIZE],
            "target": "next_object_xy",
            "intercept_radius_px": INTERCEPT_RADIUS,
        },
        "representations": [explicit, retrieval, latent, hybrid],
        "governance_posture": {
            "explicit_extracted": {
                "provenance": "current_clip_and_derived_feature_level",
                "exact_local_delete_or_correction": True,
                "global_rebuild_after_training_evidence_change": False,
            },
            "retrieval_nearest_exemplar": {
                "provenance": "direct_exemplar_ref",
                "exact_local_delete_or_correction": True,
                "global_rebuild_after_training_evidence_change": False,
            },
            "compact_learned_predictive": {
                "provenance": "training_set_and_derivation_level",
                "exact_local_delete_or_correction": False,
                "global_rebuild_after_training_evidence_change": True,
            },
            "hybrid_explicit_plus_learned": {
                "provenance": "mixed_explicit_and_training_set_level",
                "exact_local_delete_or_correction": "mixed",
                "global_rebuild_after_training_evidence_change": True,
            },
        },
        "interpretation": {
            "capability_metrics_are_not_authority": True,
            "stale_contamination_is_not_lifecycle_proof": True,
            "no_universal_winner_claim": True,
            "external_vjepa2_result_required_separately": True,
        },
    }
