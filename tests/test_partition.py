"""tests/test_partition.py - Lattice laws for the finite partition algebra.

The carriers here are small enough that every partition can be enumerated, so
the lattice properties are checked exhaustively rather than sampled.

Refinement order, bounds, greatest-lower-bound and least-upper-bound
behaviour, witness validity, and the generating-set reduction that makes the
threshold construction cheap are all covered.
"""

import pytest

from se_interpretive_kernel.partition import (
    Partition,
    all_partitions,
    join_all,
    meet_all,
)

CARRIER = ("w", "x", "y", "z")
SMALL = ("p", "q", "r")


def parts() -> list[Partition]:
    return list(all_partitions(CARRIER))


def test_enumeration_is_complete_and_distinct():
    found = parts()
    assert len(found) == 15  # Bell(4)
    assert len(set(found)) == 15


def test_bounds():
    bottom, top = Partition.discrete(CARRIER), Partition.indiscrete(CARRIER)
    for p in parts():
        assert bottom.refines(p)
        assert p.refines(top)


def test_refinement_is_a_partial_order():
    for a in parts():
        assert a.refines(a)
        for b in parts():
            if a.refines(b) and b.refines(a):
                assert a == b
            for c in parts():
                if a.refines(b) and b.refines(c):
                    assert a.refines(c)


@pytest.mark.parametrize("a", parts(), ids=repr)
def test_meet_is_greatest_lower_bound(a: Partition):
    for b in parts():
        m = a.meet(b)
        assert m.refines(a)
        assert m.refines(b)
        for c in parts():
            if c.refines(a) and c.refines(b):
                assert c.refines(m)


@pytest.mark.parametrize("a", parts(), ids=repr)
def test_join_is_least_upper_bound(a: Partition):
    for b in parts():
        j = a.join(b)
        assert a.refines(j)
        assert b.refines(j)
        for c in parts():
            if a.refines(c) and b.refines(c):
                assert j.refines(c)


def test_meet_and_join_identities():
    assert meet_all(CARRIER, []) == Partition.indiscrete(CARRIER)
    assert join_all(CARRIER, []) == Partition.discrete(CARRIER)
    for p in parts():
        assert meet_all(CARRIER, [p]) == p
        assert join_all(CARRIER, [p]) == p


def test_labels_are_canonical_regardless_of_supplied_keys():
    a = Partition.from_labels(SMALL, {"p": "left", "q": "left", "r": "right"})
    b = Partition.from_labels(SMALL, {"p": 7, "q": 7, "r": 0})
    assert a == b
    assert a.blocks() == (("p", "q"), ("r",))


def test_refinement_witness_is_valid_exactly_when_refinement_fails():
    for a in parts():
        for b in parts():
            w = a.refinement_witness(b)
            if a.refines(b):
                assert w is None
            else:
                assert w is not None
                left, right = w
                assert a.same(left, right)
                assert not b.same(left, right)


def test_generating_set_gives_the_same_closure():
    """A spanning forest generates the same equivalence as the full relation."""
    for p in parts():
        spanning = [
            (block[i], block[i + 1])
            for block in p.blocks()
            for i in range(len(block) - 1)
        ]
        full = [(x, y) for block in p.blocks() for x in block for y in block]
        assert Partition.from_pairs(CARRIER, spanning) == p
        assert Partition.from_pairs(CARRIER, full) == p


def test_from_blocks_leaves_unnamed_elements_alone():
    p = Partition.from_blocks(CARRIER, [("w", "y")])
    assert p.blocks() == (("w", "y"), ("x",), ("z",))


def test_cross_carrier_comparison_is_rejected():
    a = Partition.discrete(CARRIER)
    b = Partition.discrete(SMALL)
    with pytest.raises(ValueError, match="same carrier"):
        a.refines(b)
    with pytest.raises(ValueError, match="same carrier"):
        a.meet(b)
    with pytest.raises(ValueError, match="same carrier"):
        a.join(b)


def test_duplicate_carrier_elements_are_rejected():
    with pytest.raises(ValueError, match="distinct"):
        Partition.discrete(("a", "a"))
