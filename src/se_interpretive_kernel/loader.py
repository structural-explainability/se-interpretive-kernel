"""loader.py - Build an Artifact and a frame regime from tabular data.

The theory needs a total interpretation: every probe must produce an output for
every frame. Real tables have empty cells, so this module makes the answer to
"what does an empty cell produce" an explicit, reported choice instead of a
silent default.

Probe columns are supplied already computed. This module does not normalize,
clean, or interpret values. Normalization is the consumer's declared probe.

Missing values. An empty cell becomes the output :class:`Absent`. Two policies
decide whether different empty cells are the same output:

- ``MissingPolicy.DISTINCT`` (default): each empty cell is its own output. An
  empty cell never agrees with anything, so an unknown value is not treated as
  evidence of sameness.
- ``MissingPolicy.SHARED``: all empty cells of a probe are one output. Records
  with no value then agree with each other. In the generated regime this one
  output can also join every value of every record that the frame regime groups
  with an empty-cell record, so it can chain unrelated values together.

Neither policy is correct in general. Run both and compare the results.

Output space. By default an output carries the name of its probe column, so
equal text in two different columns is two different outputs. With
``shared_outputs=True`` equal text is one output across columns, which is
appropriate only when the probe columns are alternative readings of one field.

This module reports what was loaded. It does not judge whether a table, a
probe, or a clustering is right.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .artifact import Artifact
from .partition import Item, Partition


class MissingPolicy(Enum):
    """Decide whether different empty cells are the same output."""

    DISTINCT = "distinct"
    SHARED = "shared"


@dataclass(frozen=True)
class Observed:
    """Contain an output that was read from a non-empty cell.

    ``scope`` is the probe column, or None when outputs are shared across
    columns.
    """

    scope: str | None
    text: str


@dataclass(frozen=True)
class Absent:
    """Contain the output of an empty cell.

    ``frame`` identifies the cell under ``MissingPolicy.DISTINCT`` and is None
    under ``MissingPolicy.SHARED``.
    """

    scope: str | None
    frame: Item | None


@dataclass(frozen=True)
class Loaded:
    """Contain a loaded artifact and what was decided while loading it."""

    artifact: Artifact
    policy: MissingPolicy
    shared_outputs: bool
    missing_counts: Mapping[str, int]


def load_artifact(
    rows: Iterable[Mapping[str, str | None]],
    id_column: str,
    probe_columns: Sequence[str],
    *,
    missing_values: frozenset[str] = frozenset({""}),
    policy: MissingPolicy = MissingPolicy.DISTINCT,
    shared_outputs: bool = False,
    label: str = "",
) -> Loaded:
    """Return an artifact whose frames are the row ids and probes are columns.

    A cell is empty when it is None or exactly one of ``missing_values``.
    Values are compared exactly: no trimming or case folding is applied.
    Frame order is row order. A duplicate or empty id is an error.
    """
    columns = tuple(probe_columns)
    if not columns:
        msg = "at least one probe column is required"
        raise ValueError(msg)
    if len(set(columns)) != len(columns):
        msg = "probe columns must be distinct"
        raise ValueError(msg)
    if id_column in columns:
        msg = "the id column cannot also be a probe column"
        raise ValueError(msg)

    frames: list[Item] = []
    seen: set[str] = set()
    table: dict[tuple[Item, Item], Item] = {}
    missing_counts = {column: 0 for column in columns}
    outputs: dict[Item, None] = {}

    for number, row in enumerate(rows, start=1):
        if id_column not in row:
            msg = f"row {number}: no column {id_column!r}"
            raise ValueError(msg)
        frame = row[id_column]
        if frame is None or frame == "":
            msg = f"row {number}: empty id"
            raise ValueError(msg)
        if frame in seen:
            msg = f"row {number}: duplicate id {frame!r}"
            raise ValueError(msg)
        seen.add(frame)
        frames.append(frame)
        for column in columns:
            if column not in row:
                msg = f"row {number}: no column {column!r}"
                raise ValueError(msg)
            text = row[column]
            scope = None if shared_outputs else column
            output: Item
            if text is None or text in missing_values:
                missing_counts[column] += 1
                cell = frame if policy is MissingPolicy.DISTINCT else None
                output = Absent(scope, cell)
            else:
                output = Observed(scope, text)
            table[(column, frame)] = output
            outputs[output] = None

    if not frames:
        msg = "no rows"
        raise ValueError(msg)
    artifact = Artifact(tuple(frames), tuple(outputs), columns, table, label)
    return Loaded(artifact, policy, shared_outputs, missing_counts)


def _read_csv(path: str | Path, required: Sequence[str]) -> list[dict[str, str | None]]:
    """Return the rows of a UTF-8 CSV file, checking that columns exist."""
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        for column in required:
            if column not in header:
                msg = f"column {column!r} not found in {path}"
                raise ValueError(msg)
        return [dict(row) for row in reader]


def load_artifact_csv(
    path: str | Path,
    id_column: str,
    probe_columns: Sequence[str],
    *,
    missing_values: frozenset[str] = frozenset({""}),
    policy: MissingPolicy = MissingPolicy.DISTINCT,
    shared_outputs: bool = False,
    label: str = "",
) -> Loaded:
    """Return :func:`load_artifact` applied to the rows of a UTF-8 CSV file."""
    rows = _read_csv(path, [id_column, *probe_columns])
    return load_artifact(
        rows,
        id_column,
        probe_columns,
        missing_values=missing_values,
        policy=policy,
        shared_outputs=shared_outputs,
        label=label,
    )


def regime_from_rows(
    rows: Iterable[Mapping[str, str | None]],
    frames: Sequence[Item],
    id_column: str,
    cluster_column: str,
) -> Partition:
    """Return the frame regime declared by a clustering column.

    Records with the same cluster value are in one block. A record with an empty
    cluster value is alone in its own block. The clustering is taken as declared
    by whoever produced it; nothing here judges it.

    Every frame must appear exactly once, and no other ids may appear.
    """
    labels: dict[Item, object] = {}
    for number, row in enumerate(rows, start=1):
        frame = row.get(id_column)
        if frame is None or frame == "":
            msg = f"row {number}: empty id"
            raise ValueError(msg)
        if frame in labels:
            msg = f"row {number}: duplicate id {frame!r}"
            raise ValueError(msg)
        cluster = row.get(cluster_column)
        if cluster is None or cluster == "":
            labels[frame] = ("unclustered", frame)
        else:
            labels[frame] = ("cluster", cluster)
    known = set(frames)
    extra = [frame for frame in labels if frame not in known]
    if extra:
        msg = f"ids not in the artifact: {extra[:3]!r}"
        raise ValueError(msg)
    absent = [frame for frame in frames if frame not in labels]
    if absent:
        msg = f"artifact frames with no clustering row: {absent[:3]!r}"
        raise ValueError(msg)
    return Partition.from_labels(frames, labels)


def load_regime_csv(
    path: str | Path,
    frames: Sequence[Item],
    id_column: str,
    cluster_column: str,
) -> Partition:
    """Return :func:`regime_from_rows` applied to the rows of a UTF-8 CSV file."""
    rows = _read_csv(path, [id_column, cluster_column])
    return regime_from_rows(rows, frames, id_column, cluster_column)
