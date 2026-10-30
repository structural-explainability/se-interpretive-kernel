"""cases.py - Finite cases mirroring the Lean examples.

Each function returns an :class:`Artifact`, using the same carriers and
interpretation as the corresponding Lean example in
``SETest/InterpretiveKernel``. The assertions about these cases live in
``check.py``.

Lean names are given in each docstring. Carriers of size 2 or 3 use integers;
Booleans are written 0 and 1.
"""

from collections.abc import Sequence

from .artifact import Artifact
from .partition import Item, Partition


def _table(frames, probes, rule):
    """Return the table {(p, f): rule(p, f)}."""
    return {(p, f): rule(p, f) for p in probes for f in frames}


def example_a() -> Artifact:
    """Return Example A: four frames, parity regime, XOR interpretation."""
    frames, probes, outputs = (0, 1, 2, 3), (0, 1), (0, 1)
    return Artifact(
        frames, outputs, probes, _table(frames, probes, lambda p, f: p ^ (f % 2)), "A"
    )


def example_b() -> Artifact:
    """Return Example B: identity interpretation with a single probe."""
    frames, probes, outputs = (0, 1), ("p",), (0, 1)
    return Artifact(
        frames, outputs, probes, _table(frames, probes, lambda _p, f: f), "B"
    )


def example_c() -> Artifact:
    """Return Example C: the interpretation only records whether the frame is 0."""
    frames, probes, outputs = (0, 1, 2), (0, 1), (0, 1)
    return Artifact(
        frames, outputs, probes, _table(frames, probes, lambda _p, f: int(f == 0)), "C"
    )


def example_d() -> Artifact:
    """Return Example D: I(p, f) = p and f, so probe 0 erases the frame."""
    frames, probes, outputs = (0, 1), (0, 1), (0, 1)
    return Artifact(
        frames, outputs, probes, _table(frames, probes, lambda p, f: p & f), "D"
    )


def example_e() -> Artifact:
    """Return Example E: two probes whose images chain 0~1 and 1~2."""
    frames, probes, outputs = (0, 1), (0, 1), (0, 1, 2)

    def rule(p: int, f: int) -> int:
        return (2 if f else 1) if p else (1 if f else 0)

    return Artifact(frames, outputs, probes, _table(frames, probes, rule), "E")


def example_f() -> Artifact:
    """Return Example F: one frame, constant output, so the counit is strict."""
    frames, probes, outputs = (0,), ("p",), (0, 1)
    return Artifact(
        frames, outputs, probes, _table(frames, probes, lambda _p, _f: 0), "F"
    )


def example_g() -> Artifact:
    """Return Example G: K need not preserve joins."""
    frames, probes, outputs = (0, 1), ("p",), (0, 1, 2)
    return Artifact(
        frames,
        outputs,
        probes,
        _table(frames, probes, lambda _p, f: 0 if f == 0 else 2),
        "G",
    )


def example_h() -> Artifact:
    """Return Example H: L need not preserve meets."""
    frames, probes, outputs = (0, 1, 2), ("p",), (0, 1)
    return Artifact(
        frames, outputs, probes, _table(frames, probes, lambda _p, f: int(f != 0)), "H"
    )


def example_i() -> Artifact:
    """Return Example I: identity interpretation, incomparable thresholds."""
    frames, probes, outputs = (0, 1, 2), ("p",), (0, 1, 2)
    return Artifact(
        frames, outputs, probes, _table(frames, probes, lambda _p, f: f), "I"
    )


def merge(carrier: Sequence[Item], a: Item, b: Item) -> Partition:
    """Return the partition of ``carrier`` that merges only ``a`` and ``b``."""
    return Partition.from_pairs(carrier, [(a, b)])


def all_cases() -> list[Artifact]:
    """Return every example artifact."""
    return [
        example_a(),
        example_b(),
        example_c(),
        example_d(),
        example_e(),
        example_f(),
        example_g(),
        example_h(),
        example_i(),
    ]
