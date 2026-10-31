"""kernel.py - The interpretation-induced kernel K_Q(rho) and coherence.

Definition (Lean: ``kernelRel``). For a selected probe family Q and an
occurrence regime rho on the outputs,

    F K_Q(rho) F'   iff   for every selected probe p, I(p,F) rho I(p,F').

Construction. This module builds the kernel from probe signatures: each frame
is labeled by the tuple of rho-block numbers its selected probes produce, and
frames with equal labels share a block. This is the kernel of the signature
map, which is the paper's definition.

With no selected probes every frame has the empty signature, so the kernel is
the indiscrete partition (Lean: ``kernelRel_noProbes``).
"""

from __future__ import annotations

from collections.abc import Sequence

from .artifact import Artifact
from .partition import Item, Partition


def kernel(artifact: Artifact, selected: Sequence[Item], rho: Partition) -> Partition:
    """Return K_Q(rho), a partition of the frames.

    ``selected`` is the selected probe family Q, a subset of the artifact's
    probes. ``rho`` is a partition of the artifact's outputs.
    """
    artifact.require_selected(selected)
    if rho.carrier != artifact.outputs:
        msg = "rho must be a partition of the artifact's outputs, in order"
        raise ValueError(msg)
    signature: dict[Item, object] = {}
    for frame in artifact.frames:
        signature[frame] = tuple(
            rho.label_of(artifact.interpret(probe, frame)) for probe in selected
        )
    return Partition.from_labels(artifact.frames, signature)


def coherent(
    artifact: Artifact, selected: Sequence[Item], phi: Partition, rho: Partition
) -> bool:
    """Return whether phi is coherent with rho: phi refines K_Q(rho).

    Coherence is mathematical compatibility only. It holds trivially when rho
    is indiscrete or when no probes are selected, so it is informative only
    relative to a justified rho and Q.
    """
    return phi.refines(kernel(artifact, selected, rho))
