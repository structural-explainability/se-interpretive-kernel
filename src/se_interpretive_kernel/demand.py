"""demand.py - Pairwise interpretive demand.

Definition (Lean: ``demand``). The demand of a pair of frames (x, y) is the
least occurrence regime under which every selected probe treats x and y alike:

    delta(x, y) = equivalence closure of {(I(p,x), I(p,y)) | p selected}.

Theorem (Lean: ``kernelRel_iff_demand_finer``). For every occurrence regime
rho, F K_Q(rho) F' exactly when delta(F, F') refines rho.

delta is a generalized pseudo-ultrametric: it is the bottom partition on the
diagonal, symmetric, and satisfies the strong triangle inequality
delta(x,z) <= delta(x,y) join delta(y,z). Distinct frames may have zero
demand, so delta does not recover identity of frames.
"""

from collections.abc import Sequence

from .artifact import Artifact
from .partition import Item, Pair, Partition


def demand(artifact: Artifact, selected: Sequence[Item], x: Item, y: Item) -> Partition:
    """Return the pairwise interpretive demand delta(x, y)."""
    artifact.require_selected(selected)
    pairs: list[Pair] = []
    for probe in selected:
        pairs.append((artifact.interpret(probe, x), artifact.interpret(probe, y)))
    return Partition.from_pairs(artifact.outputs, pairs)


def kernel_from_demand(
    artifact: Artifact, selected: Sequence[Item], rho: Partition
) -> Partition:
    """Return K_Q(rho) computed as {(x, y) | delta(x, y) refines rho}."""
    pairs: list[Pair] = []
    for x in artifact.frames:
        for y in artifact.frames:
            if demand(artifact, selected, x, y).refines(rho):
                pairs.append((x, y))
    return Partition.from_pairs(artifact.frames, pairs)


def ultrametric_violations(artifact: Artifact, selected: Sequence[Item]) -> list[str]:
    """Return a description of every violated ultrametric law."""
    bottom = Partition.discrete(artifact.outputs)
    found: list[str] = []
    for x in artifact.frames:
        if demand(artifact, selected, x, x) != bottom:
            found.append(f"zero: demand({x!r}, {x!r}) is not discrete")
    for x in artifact.frames:
        for y in artifact.frames:
            if demand(artifact, selected, x, y) != demand(artifact, selected, y, x):
                found.append(f"symmetry: demand({x!r}, {y!r}) differs from reverse")
    for x in artifact.frames:
        for y in artifact.frames:
            for z in artifact.frames:
                direct = demand(artifact, selected, x, z)
                detour = demand(artifact, selected, x, y).join(
                    demand(artifact, selected, y, z)
                )
                if not direct.refines(detour):
                    found.append(f"triangle: ({x!r}, {y!r}, {z!r})")
    return found
