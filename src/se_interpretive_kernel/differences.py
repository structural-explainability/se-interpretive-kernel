"""differences.py - Report where two frame regimes disagree.

Given two declared groupings of the same frames, this module lists the groups
one regime makes that the other regime splits.

It reports differences. It does not say which regime is correct, which is
closer to some truth, or which should be preferred. Deciding that needs
evidence outside this package.
"""

from __future__ import annotations

from dataclasses import dataclass

from .partition import Item, Partition


@dataclass(frozen=True)
class Difference:
    """Contain one group made by one regime and split by the other.

    ``grouped_by`` is ``"first"`` or ``"second"``: the regime that puts
    ``frames`` in one block. ``split_into`` is how the other regime separates
    those frames, as parts that each stay together under both regimes.
    """

    grouped_by: str
    frames: tuple[Item, ...]
    split_into: tuple[tuple[Item, ...], ...]


def _splits(block: tuple[Item, ...], common: Partition) -> tuple[tuple[Item, ...], ...]:
    """Return the parts of ``block`` under a partition, in first-seen order."""
    parts: dict[int, list[Item]] = {}
    for frame in block:
        parts.setdefault(common.label_of(frame), []).append(frame)
    return tuple(tuple(part) for part in parts.values())


def regime_differences(first: Partition, second: Partition) -> list[Difference]:
    """Return every group that one regime makes and the other splits.

    An empty list means the two regimes are the same partition.
    """
    if first.carrier != second.carrier:
        msg = "both regimes must be partitions of the same frames, in order"
        raise ValueError(msg)
    common = first.meet(second)
    found: list[Difference] = []
    for block in first.blocks():
        parts = _splits(block, common)
        if len(parts) > 1:
            found.append(Difference("first", block, parts))
    for block in second.blocks():
        parts = _splits(block, common)
        if len(parts) > 1:
            found.append(Difference("second", block, parts))
    return found


def format_differences(differences: list[Difference]) -> str:
    """Return the differences as plain text, one line each."""
    lines: list[str] = []
    for item in differences:
        parts = " | ".join(", ".join(repr(f) for f in part) for part in item.split_into)
        lines.append(
            f"{item.grouped_by} groups {len(item.frames)} frames; other splits: {parts}"
        )
    return "\n".join(lines)
