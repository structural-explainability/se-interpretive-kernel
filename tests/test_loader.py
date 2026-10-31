"""Check the table loader, the missing-value policies, and the regime loader."""

from pathlib import Path

import pytest

from se_interpretive_kernel.artifact import Artifact
from se_interpretive_kernel.explain import explain_threshold
from se_interpretive_kernel.generated import generated
from se_interpretive_kernel.kernel import kernel
from se_interpretive_kernel.loader import (
    Absent,
    MissingPolicy,
    Observed,
    load_artifact,
    load_artifact_csv,
    load_regime_csv,
    regime_from_rows,
)
from se_interpretive_kernel.partition import Partition

ROWS = [
    {"id": "A", "name": "acme", "addr": ""},
    {"id": "B", "name": "acme", "addr": "1 main"},
    {"id": "C", "name": "zeta", "addr": ""},
]


def test_load_builds_total_table() -> None:
    """Every probe produces an output for every frame, including empty cells."""
    loaded = load_artifact(ROWS, "id", ["name", "addr"])
    artifact = loaded.artifact
    assert artifact.frames == ("A", "B", "C")
    assert artifact.probes == ("name", "addr")
    for probe in artifact.probes:
        for frame in artifact.frames:
            assert artifact.interpret(probe, frame) in set(artifact.outputs)
    assert loaded.missing_counts == {"name": 0, "addr": 2}
    assert artifact.interpret("name", "A") == Observed("name", "acme")


def test_distinct_policy_never_agrees_on_empty_cells() -> None:
    """Under the default policy two empty cells are different outputs."""
    artifact = load_artifact(ROWS, "id", ["addr"]).artifact
    assert artifact.interpret("addr", "A") == Absent("addr", "A")
    assert artifact.interpret("addr", "A") != artifact.interpret("addr", "C")
    rho = Partition.discrete(artifact.outputs)
    assert not kernel(artifact, ["addr"], rho).same("A", "C")


def test_shared_policy_makes_empty_cells_agree() -> None:
    """Under the shared policy all empty cells of a probe are one output."""
    loaded = load_artifact(ROWS, "id", ["addr"], policy=MissingPolicy.SHARED)
    artifact = loaded.artifact
    assert artifact.interpret("addr", "A") == artifact.interpret("addr", "C")
    rho = Partition.discrete(artifact.outputs)
    assert kernel(artifact, ["addr"], rho).same("A", "C")


def test_shared_policy_can_chain_unrelated_values() -> None:
    """A shared empty output joins values of otherwise unrelated records."""
    rows = [
        {"id": "A", "addr": ""},
        {"id": "B", "addr": "1 main"},
        {"id": "D", "addr": ""},
        {"id": "E", "addr": "2 oak"},
    ]
    one = Observed("addr", "1 main")
    two = Observed("addr", "2 oak")
    for policy, chained in (
        (MissingPolicy.SHARED, True),
        (MissingPolicy.DISTINCT, False),
    ):
        artifact = load_artifact(rows, "id", ["addr"], policy=policy).artifact
        phi = Partition.from_blocks(artifact.frames, [("A", "B"), ("D", "E")])
        assert generated(artifact, ["addr"], phi).same(one, two) is chained


def test_output_scope() -> None:
    """Equal text in two columns is two outputs unless outputs are shared."""
    rows = [{"id": "A", "x": "same", "y": "same"}]
    scoped = load_artifact(rows, "id", ["x", "y"]).artifact
    assert scoped.interpret("x", "A") != scoped.interpret("y", "A")
    shared = load_artifact(rows, "id", ["x", "y"], shared_outputs=True).artifact
    assert shared.interpret("x", "A") == shared.interpret("y", "A")


def test_none_and_custom_missing_values() -> None:
    """A short row (None) and any declared missing marker count as empty."""
    rows = [{"id": "A", "v": None}, {"id": "B", "v": "NA"}, {"id": "C", "v": "ok"}]
    loaded = load_artifact(rows, "id", ["v"], missing_values=frozenset({"", "NA"}))
    assert loaded.missing_counts == {"v": 2}
    plain = load_artifact(rows, "id", ["v"])
    assert plain.missing_counts == {"v": 1}
    assert plain.artifact.interpret("v", "B") == Observed("v", "NA")


def test_load_rejects_bad_input() -> None:
    """Bad ids, columns, and shapes are errors that name the problem."""
    with pytest.raises(ValueError, match="duplicate id"):
        load_artifact([{"id": "A", "v": "x"}, {"id": "A", "v": "y"}], "id", ["v"])
    with pytest.raises(ValueError, match="empty id"):
        load_artifact([{"id": "", "v": "x"}], "id", ["v"])
    with pytest.raises(ValueError, match="no column"):
        load_artifact([{"id": "A"}], "id", ["v"])
    with pytest.raises(ValueError, match="no rows"):
        load_artifact([], "id", ["v"])
    with pytest.raises(ValueError, match="at least one"):
        load_artifact(ROWS, "id", [])
    with pytest.raises(ValueError, match="distinct"):
        load_artifact(ROWS, "id", ["name", "name"])
    with pytest.raises(ValueError, match="cannot also"):
        load_artifact(ROWS, "id", ["id"])


def test_csv_round_trip(tmp_path: Path) -> None:
    """A CSV file loads to the same artifact as the equivalent rows."""
    path = tmp_path / "vendors.csv"
    path.write_text("id,name,addr\nA,acme,\nB,acme,1 main\nC,zeta,\n", encoding="utf-8")
    from_file = load_artifact_csv(path, "id", ["name", "addr"])
    from_rows = load_artifact(ROWS, "id", ["name", "addr"])
    assert from_file.artifact == from_rows.artifact
    with pytest.raises(ValueError, match="not found"):
        load_artifact_csv(path, "id", ["nope"])


def test_regime_from_clustering_column(tmp_path: Path) -> None:
    """A cluster column becomes a frame regime; an empty cluster is alone."""
    artifact = load_artifact(ROWS, "id", ["name"]).artifact
    path = tmp_path / "clusters.csv"
    path.write_text("id,cluster\nA,1\nB,1\nC,\n", encoding="utf-8")
    regime = load_regime_csv(path, artifact.frames, "id", "cluster")
    assert regime.same("A", "B")
    assert not regime.same("A", "C")
    two_alone = regime_from_rows(
        [{"id": "A", "c": ""}, {"id": "B", "c": ""}, {"id": "C", "c": "1"}],
        artifact.frames,
        "id",
        "c",
    )
    assert not two_alone.same("A", "B")
    rows = [{"id": "A", "c": "1"}, {"id": "B", "c": "1"}]
    with pytest.raises(ValueError, match="no clustering row"):
        regime_from_rows(rows, artifact.frames, "id", "c")
    extra = [*rows, {"id": "C", "c": ""}, {"id": "Z", "c": "9"}]
    with pytest.raises(ValueError, match="not in the artifact"):
        regime_from_rows(extra, artifact.frames, "id", "c")


def test_pipeline_runs_on_loaded_data() -> None:
    """Kernel, threshold, and explanations run end to end on loaded rows."""
    artifact = load_artifact(ROWS, "id", ["name", "addr"]).artifact
    phi = regime_from_rows(
        [{"id": "A", "c": "1"}, {"id": "B", "c": "1"}, {"id": "C", "c": ""}],
        artifact.frames,
        "id",
        "c",
    )
    threshold = generated(artifact, artifact.probes, phi)
    assert threshold.same(Absent("addr", "A"), Observed("addr", "1 main"))
    explanations = explain_threshold(artifact, artifact.probes, phi)
    assert len(explanations) == sum(len(b) - 1 for b in threshold.blocks())


def test_explain_threshold_builds_the_graph_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The work is linear in frames and probes, not in forced identifications."""
    size = 400
    rows = [
        {"id": str(i), "p": f"v{i // 4}{'a' if i % 2 == 0 else 'b'}"}
        for i in range(size)
    ]
    artifact = load_artifact(rows, "id", ["p"]).artifact
    phi = Partition.from_labels(artifact.frames, {str(i): i // 4 for i in range(size)})
    calls = 0
    original = Artifact.interpret

    def counting(self: Artifact, probe: object, frame: object) -> object:
        nonlocal calls
        calls += 1
        return original(self, probe, frame)

    monkeypatch.setattr(Artifact, "interpret", counting)
    explanations = explain_threshold(artifact, artifact.probes, phi)
    assert len(explanations) == size // 4
    assert calls <= 8 * size * len(artifact.probes)
