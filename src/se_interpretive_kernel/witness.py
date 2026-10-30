"""witness.py - Finite incompatibility witnesses.

A witness against coherence of phi with rho (Lean:
``IncompatibilityWitness``) consists of two frames related by phi, a selected
probe, and the two outputs, which rho does not relate.

A witness shows that the supplied phi, rho, probes, and interpretation are
incompatible. It does not show which of them is the faulty choice.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from .artifact import Artifact
from .partition import Item, Partition


@dataclass(frozen=True)
class Witness:
    """Contain one finite incompatibility witness."""

    frame_1: Item
    frame_2: Item
    probe: Item
    output_1: Item
    output_2: Item


def find_witness(
    artifact: Artifact, selected: Sequence[Item], phi: Partition, rho: Partition
) -> Witness | None:
    """Return a witness against coherence, or None when phi is coherent.

    Within each block of phi the first frame is compared with every later
    frame. This finds a witness whenever one exists: if the first frame agrees
    with each later frame under every selected probe, transitivity of rho gives
    agreement for every pair in the block.
    """
    artifact.require_selected(selected)
    for block in phi.blocks():
        anchor = block[0]
        for frame in block[1:]:
            for probe in selected:
                out_anchor = artifact.interpret(probe, anchor)
                out_frame = artifact.interpret(probe, frame)
                if not rho.same(out_anchor, out_frame):
                    return Witness(anchor, frame, probe, out_anchor, out_frame)
    return None


def witness_is_valid(
    artifact: Artifact,
    selected: Sequence[Item],
    phi: Partition,
    rho: Partition,
    witness: Witness,
) -> bool:
    """Return whether a witness satisfies the definition of a witness."""
    if witness.probe not in set(selected):
        return False
    if not phi.same(witness.frame_1, witness.frame_2):
        return False
    if artifact.interpret(witness.probe, witness.frame_1) != witness.output_1:
        return False
    if artifact.interpret(witness.probe, witness.frame_2) != witness.output_2:
        return False
    return not rho.same(witness.output_1, witness.output_2)
