"""Deterministic three-stage visual workload for the #246 benchmark."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .operational_memory_benchmark import FRAMES, SIZE

VERSION = "2.0.0"
SEED = 2462026
STAGES = 3
HORIZONS = 3
TRAIN_EPISODES = 64
TEST_EPISODES = 32
VELOCITIES = np.asarray(
    [(-1.0, 0.0), (1.0, 0.0), (0.0, -1.0), (0.0, 1.0),
     (-1.0, -1.0), (-1.0, 1.0), (1.0, -1.0), (1.0, 1.0)],
    dtype=np.float32,
)


@dataclass(frozen=True)
class Dataset:
    train_videos: np.ndarray
    train_targets: np.ndarray
    train_old_targets: np.ndarray
    train_corrected: np.ndarray
    train_ids: tuple[str, ...]
    test_videos: np.ndarray
    test_targets: np.ndarray
    test_old_targets: np.ndarray
    test_corrected: np.ndarray
    test_ids: tuple[str, ...]


def _draw(frame: np.ndarray, point: np.ndarray, color: tuple[int, int, int], radius: int) -> None:
    x, y = int(round(float(point[0]))), int(round(float(point[1])))
    frame[max(0, y-radius):min(SIZE, y+radius+1), max(0, x-radius):min(SIZE, x+radius+1)] = color


def _clip(start: np.ndarray, velocity: np.ndarray, stale_velocity: np.ndarray | None) -> tuple[np.ndarray, np.ndarray]:
    video = np.zeros((FRAMES, SIZE, SIZE, 3), dtype=np.uint8)
    gradient = np.linspace(7, 25, SIZE, dtype=np.uint8)
    for t in range(FRAMES):
        frame = video[t]
        frame[..., 0] = gradient
        frame[..., 1] = gradient[::-1]
        frame[..., 2] = 10
        _draw(frame, start + velocity * t, (242, 34, 30), 2)
        if stale_velocity is not None:
            _draw(frame, start + stale_velocity * t, (118, 46, 150), 1)
    # The next stage begins at t=FRAMES. The final observed point in this clip
    # is t=FRAMES-1, so this returned position is also forecast horizon 1.
    return video, start + velocity * FRAMES


def _episode(rng: np.random.Generator, index: int):
    corrected = index % 2 == 1
    v0 = VELOCITIES[int(rng.integers(0, len(VELOCITIES)))]
    v1 = v0
    if corrected:
        alternatives = [v for v in VELOCITIES if not np.array_equal(v, v0)]
        v1 = alternatives[int(rng.integers(0, len(alternatives)))]
    position = np.asarray([rng.integers(20, 44), rng.integers(20, 44)], dtype=np.float32)
    videos, targets, old_targets = [], [], []
    # `position` returned by _clip is already the first unobserved point.
    # Therefore horizon 1 has offset 0 from that position, horizon 2 offset 1,
    # and so on. Starting this vector at 1 would skip the first unobserved
    # state and bias every representation by one time step.
    future_offsets = np.arange(HORIZONS, dtype=np.float32)[:, None]
    for stage in range(STAGES):
        active = v0 if stage == 0 else v1
        video, position = _clip(position, active, v0 if corrected and stage > 0 else None)
        videos.append(video)
        targets.append(position[None, :] + future_offsets * active[None, :])
        old_targets.append(position[None, :] + future_offsets * v0[None, :])
    return np.stack(videos), np.stack(targets), np.stack(old_targets), corrected


def make_dataset(seed: int = SEED) -> Dataset:
    rng = np.random.default_rng(seed)

    def build(count: int, split: str):
        videos, targets, old, corrected, ids = [], [], [], [], []
        for index in range(count):
            episode = _episode(rng, index)
            videos.append(episode[0]); targets.append(episode[1]); old.append(episode[2]); corrected.append(episode[3])
            ids.append(f"long-horizon:{VERSION}:{split}:{index:03d}")
        return np.stack(videos), np.stack(targets), np.stack(old), np.asarray(corrected, dtype=bool), tuple(ids)

    return Dataset(*build(TRAIN_EPISODES, "train"), *build(TEST_EPISODES, "test"))
