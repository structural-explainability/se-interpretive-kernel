"""sampling.py - Random small artifacts for property checks.

Deterministic for a given seed. Sizes are kept small so that exhaustive
enumeration of partitions of the outputs and the frames stays cheap.
"""

from __future__ import annotations

from collections.abc import Iterator
from random import Random

from .artifact import Artifact
from .partition import Item


def random_artifact(
    rng: Random, max_frames: int = 4, max_outputs: int = 4, max_probes: int = 3
) -> Artifact:
    """Return a random total artifact of small size."""
    n_frames = rng.randint(1, max_frames)
    n_outputs = rng.randint(1, max_outputs)
    n_probes = rng.randint(0, max_probes)
    frames = tuple(range(n_frames))
    outputs = tuple(range(n_outputs))
    probes = tuple(f"p{i}" for i in range(n_probes))
    table: dict[tuple[Item, Item], Item] = {
        (p, f): rng.choice(outputs) for p in probes for f in frames
    }
    return Artifact(frames, outputs, probes, table, "random")


def random_artifacts(count: int, seed: int) -> Iterator[Artifact]:
    """Yield ``count`` random artifacts for the given seed."""
    rng = Random(seed)
    for _ in range(count):
        yield random_artifact(rng)
