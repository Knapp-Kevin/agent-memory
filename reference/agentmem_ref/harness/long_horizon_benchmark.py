"""Matched explicit/retrieval/learned/hybrid evaluator for #246."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

import numpy as np

from .long_horizon_dataset import Dataset, HORIZONS, STAGES, VERSION, make_dataset
from .operational_memory_benchmark import (
    FRAMES, SIZE, explicit_features, fit_standardized_ridge,
    nearest_neighbor_predict, pooled_clip_descriptor, predict_ridge,
)

SUCCESS_RADIUS = 3.0


def clip_descriptors(videos: np.ndarray) -> np.ndarray:
    n = len(videos)
    flat = videos.reshape(n * STAGES, FRAMES, SIZE, SIZE, 3)
    return pooled_clip_descriptor(flat).reshape(n, STAGES, -1)


def explicit_state(videos: np.ndarray) -> np.ndarray:
    n = len(videos)
    raw = explicit_features(videos.reshape(n * STAGES, FRAMES, SIZE, SIZE, 3)).reshape(n, STAGES, FRAMES, 3)
    state = np.zeros((n, STAGES, 4), dtype=np.float32)
    for i in range(n):
        for stage in range(STAGES):
            obs = [np.asarray([row[0] * SIZE, row[1] * SIZE], dtype=np.float32) for row in raw[i, stage] if row[2] > 0.5]
            if obs:
                state[i, stage, :2] = obs[-1]
            if len(obs) >= 2:
                state[i, stage, 2:] = obs[-1] - obs[-2]
    return state


def explicit_plan(state: np.ndarray) -> np.ndarray:
    horizon = np.arange(1, HORIZONS + 1, dtype=np.float32)[:, None]
    result = np.zeros((len(state), STAGES, HORIZONS, 2), dtype=np.float32)
    for stage in range(STAGES):
        result[:, stage] = state[:, stage, None, :2] + horizon[None] * state[:, stage, None, 2:]
    return result


def cumulative(features: np.ndarray, stage: int) -> np.ndarray:
    masked = np.zeros_like(features)
    masked[:, :stage + 1] = features[:, :stage + 1]
    return masked.reshape(len(features), -1)


def target_rows(targets: np.ndarray, stage: int) -> np.ndarray:
    return targets[:, stage].reshape(len(targets), HORIZONS * 2)


def plan(values: np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=np.float32).reshape(len(values), HORIZONS, 2)


def metrics(pred: np.ndarray, target: np.ndarray, corrected: np.ndarray) -> dict[str, Any]:
    distance = np.linalg.norm(pred - target, axis=-1)
    result: dict[str, Any] = {
        "horizon_mean_error_px": [round(float(distance[:, h].mean()), 6) for h in range(HORIZONS)],
        "mean_plan_error_px": round(float(distance.mean()), 6),
        "final_success_rate": round(float((distance[:, -1] <= SUCCESS_RADIUS).mean()), 6),
        "full_plan_success_rate": round(float((distance <= SUCCESS_RADIUS).all(axis=1).mean()), 6),
    }
    if corrected.any():
        result["corrected_final_error_px"] = round(float(distance[corrected, -1].mean()), 6)
    return result


def adaptation(pred_by_stage: list[np.ndarray], targets: np.ndarray, corrected: np.ndarray) -> dict[str, float]:
    delays = []
    for i in np.nonzero(corrected)[0]:
        delay = 2
        for offset, stage in enumerate((1, 2)):
            if np.linalg.norm(pred_by_stage[stage][i, -1] - targets[i, stage, -1]) <= SUCCESS_RADIUS:
                delay = offset
                break
        delays.append(delay)
    return {
        "mean_correction_revocation_adaptation_steps": round(float(np.mean(delays)), 6),
        "recovered_by_confirmation_rate": round(float(np.mean(np.asarray(delays) <= 1)), 6),
    }


def stale_influence_rate(stale: np.ndarray, current: np.ndarray, old: np.ndarray, corrected: np.ndarray) -> float:
    if not corrected.any():
        return 0.0
    stale_final = stale[corrected, 1, -1]
    current_final = current[corrected, 1, -1]
    old_final = old[corrected, 1, -1]
    return round(float((np.linalg.norm(stale_final-old_final, axis=1) < np.linalg.norm(stale_final-current_final, axis=1)).mean()), 6)


def learned_result(name: str, train_features: np.ndarray, test_features: np.ndarray, data: Dataset) -> dict[str, Any]:
    current, stale, fit_seconds = [], [], 0.0
    for stage in range(STAGES):
        x = cumulative(train_features, stage); test_x = cumulative(test_features, stage); y = target_rows(data.train_targets, stage)
        start = time.perf_counter(); model = fit_standardized_ridge(x, y); fit_seconds += time.perf_counter() - start
        current.append(plan(predict_ridge(model, test_x)))
        if stage == 0:
            stale.append(current[-1])
        else:
            rows = np.nonzero(data.train_corrected)[0]
            sx = np.concatenate([x[rows], x]); sy = np.concatenate([target_rows(data.train_old_targets, stage)[rows], y])
            stale.append(plan(predict_ridge(fit_standardized_ridge(sx, sy), test_x)))
    current_stack, stale_stack = np.stack(current, axis=1), np.stack(stale, axis=1)
    return result_block(name, current_stack, stale_stack, current, data, fit_seconds=fit_seconds, feature_dimension=train_features.shape[-1] * STAGES)


def retrieval_result(train_features: np.ndarray, test_features: np.ndarray, data: Dataset) -> dict[str, Any]:
    current, stale = [], []
    for stage in range(STAGES):
        x = cumulative(train_features, stage); test_x = cumulative(test_features, stage); y = target_rows(data.train_targets, stage)
        current.append(plan(nearest_neighbor_predict(x, y, test_x)))
        if stage == 0:
            stale.append(current[-1])
        else:
            rows = np.nonzero(data.train_corrected)[0]
            sx = np.concatenate([x[rows], x]); sy = np.concatenate([target_rows(data.train_old_targets, stage)[rows], y])
            stale.append(plan(nearest_neighbor_predict(sx, sy, test_x)))
    return result_block("retrieval", np.stack(current, axis=1), np.stack(stale, axis=1), current, data, feature_dimension=train_features.shape[-1] * STAGES)


def result_block(name: str, current: np.ndarray, stale: np.ndarray, current_list: list[np.ndarray], data: Dataset, **extra) -> dict[str, Any]:
    return {
        "representation": name,
        "current_only": {f"stage_{s}": metrics(current[:, s], data.test_targets[:, s], data.test_corrected) for s in range(STAGES)},
        "stale_contaminated": {f"stage_{s}": metrics(stale[:, s], data.test_targets[:, s], data.test_corrected) for s in range(STAGES)},
        "recovered_current_only": {f"stage_{s}": metrics(current[:, s], data.test_targets[:, s], data.test_corrected) for s in range(STAGES)},
        "adaptation": adaptation(current_list, data.test_targets, data.test_corrected),
        "stale_influence_rate": stale_influence_rate(stale, data.test_targets, data.test_old_targets, data.test_corrected),
        **extra,
    }


def benchmark_external_features(name: str, train_features: np.ndarray, test_features: np.ndarray, dataset: Dataset | None = None) -> dict[str, Any]:
    data = dataset or make_dataset()
    if train_features.shape[:2] != (len(data.train_videos), STAGES) or test_features.shape[:2] != (len(data.test_videos), STAGES):
        raise ValueError("external features must preserve episode/stage identity")
    return learned_result(name, train_features, test_features, data)


def run_benchmark() -> dict[str, Any]:
    data = make_dataset()
    train_desc, test_desc = clip_descriptors(data.train_videos), clip_descriptors(data.test_videos)
    train_exp, test_exp = explicit_state(data.train_videos), explicit_state(data.test_videos)
    explicit_current = explicit_plan(test_exp); explicit_stale = explicit_current.copy()
    explicit_stale[data.test_corrected, 1:] = data.test_old_targets[data.test_corrected, 1:]
    explicit = result_block("explicit_extracted", explicit_current, explicit_stale, [explicit_current[:, s] for s in range(STAGES)], data, feature_dimension=train_exp.shape[-1] * STAGES)
    reps = [
        explicit,
        retrieval_result(train_desc, test_desc, data),
        learned_result("learned_compact", train_desc, test_desc, data),
        learned_result("hybrid_explicit_plus_learned", np.concatenate([train_desc, train_exp], axis=-1), np.concatenate([test_desc, test_exp], axis=-1), data),
    ]
    manifest = {
        "benchmark_version": VERSION,
        "train_ids": list(data.train_ids),
        "test_ids": list(data.test_ids),
        "corrected_test_count": int(data.test_corrected.sum()),
        "stages": STAGES,
        "horizons": HORIZONS,
        "correction_stage": 1,
        "revoked_state": "stage_0_trajectory_after_correction",
        "hidden_host_memory": "disabled_by_fixture",
    }
    digest = "sha256:" + hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "benchmark_id": "operational-memory-long-horizon-v2",
        "benchmark_version": VERSION,
        "dataset_manifest": manifest,
        "dataset_manifest_digest": digest,
        "representations": reps,
        "governance": {"stale_influence_measured": True, "correction_revocation_explicit": True, "capability_separate_from_governance": True, "conditional_memory_profile": "docs/profiles/conditional-memory-influence-profile.md"},
    }
