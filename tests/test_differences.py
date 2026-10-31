"""Check the report of differences between two frame regimes."""

import pytest

from se_interpretive_kernel.differences import format_differences, regime_differences
from se_interpretive_kernel.partition import Partition, all_partitions

FRAMES = ("a", "b", "c", "d")


def test_same_regime_has_no_differences() -> None:
    """Identical regimes report nothing."""
    regime = Partition.from_blocks(FRAMES, [("a", "b"), ("c", "d")])
    assert regime_differences(regime, regime) == []


def test_reports_each_side_that_the_other_splits() -> None:
    """A group made by one regime and split by the other is reported once."""
    first = Partition.from_blocks(FRAMES, [("a", "b", "c"), ("d",)])
    second = Partition.from_blocks(FRAMES, [("a", "b"), ("c", "d")])
    found = regime_differences(first, second)
    assert [(d.grouped_by, d.frames) for d in found] == [
        ("first", ("a", "b", "c")),
        ("second", ("c", "d")),
    ]
    assert found[0].split_into == (("a", "b"), ("c",))
    assert found[1].split_into == (("c",), ("d",))
    assert "first groups 3 frames" in format_differences(found)


def test_empty_exactly_when_regimes_are_equal() -> None:
    """For every pair of regimes on four frames, no differences means equal."""
    regimes = list(all_partitions(FRAMES))
    for first in regimes:
        for second in regimes:
            assert (regime_differences(first, second) == []) == (first == second)


def test_rejects_different_carriers() -> None:
    """Regimes over different frames cannot be compared."""
    with pytest.raises(ValueError, match="same frames"):
        regime_differences(Partition.discrete(("a",)), Partition.discrete(("b",)))
