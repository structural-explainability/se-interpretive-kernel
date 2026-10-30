"""literal.py - Independent literal definitions, used as an oracle.

Every function here works on explicit sets of ordered pairs and uses a naive
fixed-point closure. Nothing here uses :class:`Partition` internals, labels, or
the union-find, so agreement with the partition-based modules is a real
cross-check rather than a restatement.

The functions are slow and intended only for small finite cases.
"""

from collections.abc import Iterable, Sequence

from .artifact import Artifact
from .partition import Item, Pair, Partition

type PairSet = frozenset[Pair]


def pairs_of(partition: Partition) -> PairSet:
    """Return a partition as the explicit set of related ordered pairs."""
    return frozenset(
        (x, y)
        for x in partition.carrier
        for y in partition.carrier
        if partition.same(x, y)
    )


def equivalence_closure(carrier: Sequence[Item], pairs: Iterable[Pair]) -> PairSet:
    """Return the least equivalence relation containing ``pairs``.

    Starts from the identity, adds the reverse of every pair, and repeats
    composition until nothing new appears.
    """
    relation: set[Pair] = {(x, x) for x in carrier}
    for x, y in pairs:
        relation.add((x, y))
        relation.add((y, x))
    changed = True
    while changed:
        changed = False
        for x, y in list(relation):
            for y2, z in list(relation):
                if y == y2 and (x, z) not in relation:
                    relation.add((x, z))
                    changed = True
    return frozenset(relation)


def kernel_pairs(artifact: Artifact, selected: Sequence[Item], rho: PairSet) -> PairSet:
    """Return {(F, F') | for every selected p, (I(p,F), I(p,F')) in rho}."""
    return frozenset(
        (f1, f2)
        for f1 in artifact.frames
        for f2 in artifact.frames
        if all(
            (artifact.interpret(p, f1), artifact.interpret(p, f2)) in rho
            for p in selected
        )
    )


def generator_pairs(
    artifact: Artifact, selected: Sequence[Item], phi: PairSet
) -> PairSet:
    """Return {(I(p,F), I(p,F')) | p selected and (F, F') in phi}."""
    return frozenset(
        (artifact.interpret(p, f1), artifact.interpret(p, f2))
        for (f1, f2) in phi
        for p in selected
    )


def generated_pairs(
    artifact: Artifact, selected: Sequence[Item], phi: PairSet
) -> PairSet:
    """Return the equivalence closure of the generators of phi."""
    return equivalence_closure(
        artifact.outputs, generator_pairs(artifact, selected, phi)
    )


def is_subset(smaller: PairSet, larger: PairSet) -> bool:
    """Return whether one relation is contained in another."""
    return smaller <= larger
