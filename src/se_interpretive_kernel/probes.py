"""probes.py - Probe sensitivity of the kernel and the threshold.

Every result in this package is relative to the declared probe family Q. This
module reports how much each result depends on which probes are in Q.

For the kernel K_Q(rho):

- :func:`separating_probes` lists the probes that tell two frames apart.
- :func:`sole_separated_pairs` lists, for each probe, the frame pairs that no
  other selected probe separates.
- :func:`load_bearing_probes` lists the probes whose removal changes the
  kernel.
- :func:`minimal_probe_sets` lists every smallest-by-inclusion subset of Q that
  gives the same kernel.

For the threshold L_Q(phi):

- :func:`probe_contributions` gives the threshold each probe forces alone. By
  probe-union duality (Lean: ``liftRel_probeUnion``), L_Q(phi) is the join of
  these.

Nothing here decides whether the probe family is complete. It reports how the
answer moves when probes are added or removed.
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations

from .artifact import Artifact
from .generated import generated
from .kernel import kernel
from .partition import Item, Partition


def separating_probes(
    artifact: Artifact,
    selected: Sequence[Item],
    rho: Partition,
    x: Item,
    y: Item,
) -> tuple[Item, ...]:
    """Return the selected probes whose outputs for x and y rho does not relate.

    The frames x and y are related by K_Q(rho) exactly when this is empty.
    """
    artifact.require_selected(selected)
    if rho.carrier != artifact.outputs:
        msg = "rho must be a partition of the artifact's outputs, in order"
        raise ValueError(msg)
    return tuple(
        probe
        for probe in selected
        if not rho.same(artifact.interpret(probe, x), artifact.interpret(probe, y))
    )


def sole_separated_pairs(
    artifact: Artifact, selected: Sequence[Item], rho: Partition
) -> dict[Item, list[tuple[Item, Item]]]:
    """Return, for each selected probe, the frame pairs only that probe separates.

    A pair listed under probe p is related by K_Q(rho) minus p and separated by
    K_Q(rho): removing p from the family would merge the two frames. Pairs are
    listed once, in frame order. Every selected probe appears as a key, with an
    empty list when it is the sole separator of nothing.
    """
    result: dict[Item, list[tuple[Item, Item]]] = {probe: [] for probe in selected}
    frames = artifact.frames
    for i, x in enumerate(frames):
        for y in frames[i + 1 :]:
            separators = separating_probes(artifact, selected, rho, x, y)
            if len(separators) == 1:
                result[separators[0]].append((x, y))
    return result


def load_bearing_probes(
    artifact: Artifact, selected: Sequence[Item], rho: Partition
) -> tuple[Item, ...]:
    """Return the selected probes whose removal changes K_Q(rho).

    Because the kernel only gets coarser as probes are removed, a load-bearing
    probe belongs to every minimal probe set.
    """
    full = kernel(artifact, selected, rho)
    return tuple(
        probe
        for probe in selected
        if kernel(artifact, [p for p in selected if p != probe], rho) != full
    )


def minimal_probe_sets(
    artifact: Artifact, selected: Sequence[Item], rho: Partition
) -> list[tuple[Item, ...]]:
    """Return every subset of Q that gives the same kernel and has no smaller one.

    The search is exhaustive over subsets, smallest first, so it is intended
    for small probe families. :func:`load_bearing_probes` and
    :func:`sole_separated_pairs` scale polynomially and give the same
    information about single probes.
    """
    target = kernel(artifact, selected, rho)
    found: list[tuple[Item, ...]] = []
    for size in range(len(selected) + 1):
        for subset in combinations(selected, size):
            if any(set(smaller) <= set(subset) for smaller in found):
                continue
            if kernel(artifact, subset, rho) == target:
                found.append(subset)
    return found


def probe_contributions(
    artifact: Artifact, selected: Sequence[Item], phi: Partition
) -> dict[Item, Partition]:
    """Return, for each selected probe, the threshold that probe forces alone.

    The threshold of the whole family is the join of these partitions.
    """
    artifact.require_selected(selected)
    return {probe: generated(artifact, (probe,), phi) for probe in selected}
