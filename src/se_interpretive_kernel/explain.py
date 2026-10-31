"""explain.py - Derivations for the identifications a threshold forces.

The generated occurrence regime L_Q(phi) is an equivalence closure, so two
outputs are related only because a chain of generating pairs connects them.
This module returns that chain. Each step says which probe read which two
frames, that the frame regime relates those frames, and which two outputs the
probe produced.

An explanation is a finite derivation of one forced identification. It shows why
the declared frame regime obliges the outputs to be called the same under the
declared probes. It does not show that the identification is wrong or right.

The chain is found in the graph of spanning-path generating pairs (Lean:
``liftRel_eq_of_generates``), so every frame pair named in a step lies in one
block of phi. The chain is a shortest one in that graph, not necessarily the
shortest over all frame pairs.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass

from .artifact import Artifact
from .generated import generated
from .partition import Item, Partition


@dataclass(frozen=True)
class Step:
    """Contain one link of a derivation.

    ``probe`` reads ``frame_1`` as ``output_from`` and ``frame_2`` as
    ``output_to``, and the frame regime relates ``frame_1`` and ``frame_2``.
    """

    probe: Item
    frame_1: Item
    frame_2: Item
    output_from: Item
    output_to: Item


@dataclass(frozen=True)
class Explanation:
    """Contain the derivation of one forced identification."""

    output_1: Item
    output_2: Item
    steps: tuple[Step, ...]


def _check_outputs(artifact: Artifact, *outputs: Item) -> None:
    """Reject an output that the artifact does not have."""
    known = set(artifact.outputs)
    for output in outputs:
        if output not in known:
            msg = f"{output!r} is not an output of this artifact"
            raise ValueError(msg)


def _build_edges(
    artifact: Artifact, selected: Sequence[Item], phi: Partition
) -> dict[Item, list[Step]]:
    """Return, for each output, the steps that leave it.

    Built from spanning-path generating pairs. Each pair gives a step in both
    directions.
    """
    edges: dict[Item, list[Step]] = {}
    for block in phi.blocks():
        for index in range(len(block) - 1):
            first = block[index]
            second = block[index + 1]
            for probe in selected:
                out_first = artifact.interpret(probe, first)
                out_second = artifact.interpret(probe, second)
                if out_first == out_second:
                    continue
                edges.setdefault(out_first, []).append(
                    Step(probe, first, second, out_first, out_second)
                )
                edges.setdefault(out_second, []).append(
                    Step(probe, second, first, out_second, out_first)
                )
    return edges


def _search_from(
    edges: dict[Item, list[Step]], start: Item, goal: Item | None = None
) -> dict[Item, Step]:
    """Return the last step on a shortest path from start to each reached output.

    Stops early once ``goal`` is reached. With no goal it reaches everything
    connected to ``start``.
    """
    arrived_by: dict[Item, Step] = {}
    queue: deque[Item] = deque([start])
    seen: set[Item] = {start}
    while queue:
        current = queue.popleft()
        for step in edges.get(current, []):
            if step.output_to in seen:
                continue
            seen.add(step.output_to)
            arrived_by[step.output_to] = step
            if step.output_to == goal:
                return arrived_by
            queue.append(step.output_to)
    return arrived_by


def _path_to(
    arrived_by: dict[Item, Step], start: Item, goal: Item
) -> list[Step] | None:
    """Return the steps from start to goal, or None if goal was not reached."""
    if goal not in arrived_by:
        return None
    path: list[Step] = []
    node = goal
    while node != start:
        link = arrived_by[node]
        path.append(link)
        node = link.output_from
    path.reverse()
    return path


def explain(
    artifact: Artifact,
    selected: Sequence[Item],
    phi: Partition,
    a: Item,
    b: Item,
) -> list[Step] | None:
    """Return a derivation that L_Q(phi) relates a and b, or None if it does not.

    An empty list means a and b are the same output.
    """
    artifact.require_selected(selected)
    if phi.carrier != artifact.frames:
        msg = "phi must be a partition of the artifact's frames, in order"
        raise ValueError(msg)
    _check_outputs(artifact, a, b)
    if a == b:
        return []

    edges = _build_edges(artifact, selected, phi)
    return _path_to(_search_from(edges, a, b), a, b)


def steps_are_valid(
    artifact: Artifact,
    selected: Sequence[Item],
    phi: Partition,
    a: Item,
    b: Item,
    steps: Sequence[Step],
) -> bool:
    """Return whether steps form a derivation from a to b.

    Checks the definition directly: the chain starts at a, ends at b, each link
    starts where the previous one ended, every probe is selected, the frame
    regime relates the two frames of each link, and each output is what the
    probe produces.
    """
    if not steps:
        return a == b
    if steps[0].output_from != a or steps[-1].output_to != b:
        return False
    chosen = set(selected)
    previous = a
    for step in steps:
        if step.output_from != previous:
            return False
        if step.probe not in chosen:
            return False
        if not phi.same(step.frame_1, step.frame_2):
            return False
        if artifact.interpret(step.probe, step.frame_1) != step.output_from:
            return False
        if artifact.interpret(step.probe, step.frame_2) != step.output_to:
            return False
        previous = step.output_to
    return True


def explain_threshold(
    artifact: Artifact, selected: Sequence[Item], phi: Partition
) -> list[Explanation]:
    """Return a derivation for every identification the threshold forces.

    For each block of L_Q(phi) with more than one output, the first output of
    the block is explained against each other output in it. A block of size n
    gives n - 1 explanations, which together connect the whole block.
    """
    threshold = generated(artifact, selected, phi)
    edges = _build_edges(artifact, selected, phi)
    explanations: list[Explanation] = []
    for block in threshold.blocks():
        if len(block) < 2:
            continue
        anchor = block[0]
        arrived_by = _search_from(edges, anchor)
        for other in block[1:]:
            steps = _path_to(arrived_by, anchor, other)
            if steps is None:
                msg = "threshold relates outputs that no derivation connects"
                raise RuntimeError(msg)
            explanations.append(Explanation(anchor, other, tuple(steps)))
    return explanations


def format_steps(steps: Sequence[Step]) -> str:
    """Return a derivation as plain text, one line per link."""
    lines: list[str] = []
    for number, step in enumerate(steps, start=1):
        lines.append(
            f"{number}. probe {step.probe!r} reads frame {step.frame_1!r} as "
            f"{step.output_from!r} and frame {step.frame_2!r} as "
            f"{step.output_to!r}; the frame regime relates those two frames"
        )
    return "\n".join(lines)
