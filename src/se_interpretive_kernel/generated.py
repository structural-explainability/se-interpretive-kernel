"""generated.py - The generated occurrence regime L_Q(phi).

Definition (Lean: ``liftRel``). For a frame regime phi and a selected probe
family Q, the generating pairs are

    (I(p,F), I(p,F'))   for selected p and F phi F'.

L_Q(phi) is the equivalence closure of the generating pairs, the least
occurrence regime that makes phi coherent.

Terminology. In this module and in the Lean, "generated occurrence regime"
names L_Q(phi). The paper's "comparison lifting" is a different construction;
see ``lifting.py``.

Generating-set reduction (Lean: ``liftRel_eq_of_generates``). It is enough to
use a spanning path through each block of phi instead of all pairs in the
block. :func:`generated` does that; :func:`generated_all_pairs` uses every
pair and exists so the two can be compared.
"""

from __future__ import annotations

from collections.abc import Sequence

from .artifact import Artifact
from .partition import Item, Pair, Partition


def _check_inputs(artifact: Artifact, selected: Sequence[Item], phi: Partition) -> None:
    """Reject a selection or a frame regime that does not fit the artifact."""
    artifact.require_selected(selected)
    if phi.carrier != artifact.frames:
        msg = "phi must be a partition of the artifact's frames, in order"
        raise ValueError(msg)


def generating_pairs_reduced(
    artifact: Artifact, selected: Sequence[Item], phi: Partition
) -> list[Pair]:
    """Return generating pairs from a spanning path through each phi block."""
    _check_inputs(artifact, selected, phi)
    pairs: list[Pair] = []
    for block in phi.blocks():
        for index in range(len(block) - 1):
            first = block[index]
            second = block[index + 1]
            for probe in selected:
                pairs.append(
                    (
                        artifact.interpret(probe, first),
                        artifact.interpret(probe, second),
                    )
                )
    return pairs


def generating_pairs_all(
    artifact: Artifact, selected: Sequence[Item], phi: Partition
) -> list[Pair]:
    """Return generating pairs from every ordered pair inside each phi block."""
    _check_inputs(artifact, selected, phi)
    pairs: list[Pair] = []
    for block in phi.blocks():
        for first in block:
            for second in block:
                for probe in selected:
                    pairs.append(
                        (
                            artifact.interpret(probe, first),
                            artifact.interpret(probe, second),
                        )
                    )
    return pairs


def generated(
    artifact: Artifact, selected: Sequence[Item], phi: Partition
) -> Partition:
    """Return L_Q(phi) using the spanning-path generating set."""
    pairs = generating_pairs_reduced(artifact, selected, phi)
    return Partition.from_pairs(artifact.outputs, pairs)


def generated_all_pairs(
    artifact: Artifact, selected: Sequence[Item], phi: Partition
) -> Partition:
    """Return L_Q(phi) using every pair inside each block of phi."""
    pairs = generating_pairs_all(artifact, selected, phi)
    return Partition.from_pairs(artifact.outputs, pairs)


def threshold(
    artifact: Artifact, selected: Sequence[Item], phi: Partition
) -> Partition:
    """Return the interpretive threshold, which is L_Q(phi).

    An occurrence regime rho is admissible for phi exactly when this partition
    refines rho (Lean: ``admissible_iff_threshold_finer``).
    """
    return generated(artifact, selected, phi)
