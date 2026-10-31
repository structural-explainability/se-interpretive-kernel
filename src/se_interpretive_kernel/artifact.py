"""artifact.py - Finite comparison artifact for the Interpretive Kernel.

An :class:`Artifact` holds the data the theory starts from:

- a finite carrier of frames (the paper's E),
- a finite carrier of outputs (the paper's A),
- a finite set of probes (the paper's P), and
- a total interpretation table I : P x E -> A.

It holds no equivalence relations. Frame regimes and output regimes are
:class:`~se_interpretive_kernel.partition.Partition` values supplied
separately, over ``frames`` and ``outputs`` in the order stored here.

Nothing here decides which probes, frames, or outputs a domain ought to
declare, and nothing here shows that an interpretation is correct.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from se_interpretive_kernel.partition import Item


@dataclass(frozen=True)
class Artifact:
    """Contain the finite data of one comparison.

    ``table`` maps ``(probe, frame)`` to an output. It must be defined for
    every probe and frame, and every value must be an output. Totality is
    required by the theory: a missing or inapplicable result must be
    represented by a declared output value.

    ``label`` is a human-readable name for diagnostics.
    """

    frames: tuple[Item, ...]
    outputs: tuple[Item, ...]
    probes: tuple[Item, ...]
    table: Mapping[tuple[Item, Item], Item]
    label: str = ""

    def __post_init__(self) -> None:
        """Reject malformed data: duplicates, missing entries, unknown outputs."""
        if len(set(self.frames)) != len(self.frames):
            msg = "frames must be distinct"
            raise ValueError(msg)
        if len(set(self.outputs)) != len(self.outputs):
            msg = "outputs must be distinct"
            raise ValueError(msg)
        if len(set(self.probes)) != len(self.probes):
            msg = "probes must be distinct"
            raise ValueError(msg)
        output_set = set(self.outputs)
        for probe in self.probes:
            for frame in self.frames:
                key = (probe, frame)
                if key not in self.table:
                    msg = f"interpretation is not total: missing {key!r}"
                    raise ValueError(msg)
                if self.table[key] not in output_set:
                    msg = f"interpretation value {self.table[key]!r} is not an output"
                    raise ValueError(msg)

    def interpret(self, probe: Item, frame: Item) -> Item:
        """Return I(probe, frame)."""
        return self.table[(probe, frame)]

    def require_selected(self, selected: Sequence[Item]) -> None:
        """Reject a selection that names a probe the artifact does not have."""
        probe_set = set(self.probes)
        for probe in selected:
            if probe not in probe_set:
                msg = f"selected probe {probe!r} is not a probe of this artifact"
                raise ValueError(msg)
