"""tests/test_lifting.py - Comparison lifting laws and the two counterexamples.

Indexed pointwise comparison is checked exhaustively against the three cost
laws and against meet preservation.

Two comparisons are checked because they fail, and both failures are
regressions that must keep failing:

- quotient-image equality on unordered outputs is monotone but does not
  preserve meets, so no cost function represents it;
- optimal matching over bijections violates the triangle law, so it is not a
  lifting even though it is the natural reading of "the two agree under some
  matching".

The final test states the price of the repair: a declared canonicalization
restores the laws but requires an identification no finer than the best
matching would have needed.
"""

from typing import cast

from se_interpretive_kernel.lifting import (
    IndexedPointwise,
    OptimalMatching,
    QuotientImage,
    check_lifting_laws,
    check_meet_preservation,
    check_monotonicity,
)
from se_interpretive_kernel.partition import Item, Partition, all_partitions

OUT = ("a", "b", "c", "d")
TRIPLE = (0, 1, 2)


# === Indexed pointwise comparison: the selected lifting ===


def indexed() -> IndexedPointwise:
    """Compare every length-two sequence over a three-value output carrier."""
    objects = tuple((i, j) for i in TRIPLE for j in TRIPLE)
    return IndexedPointwise(
        output_carrier=TRIPLE,
        objects=objects,
        # The objects here are already indexed sequences of outputs.
        form=lambda x: cast(tuple[Item, ...], x),
    )


def test_indexed_pointwise_satisfies_the_cost_laws():
    assert check_lifting_laws(indexed()) == ()


def test_indexed_pointwise_preserves_meets():
    samples = list(all_partitions(TRIPLE))
    assert len(samples) == 5  # Bell(3)
    assert check_meet_preservation(indexed(), samples) == ()


def test_indexed_pointwise_is_monotone():
    samples = list(all_partitions(TRIPLE))
    assert check_monotonicity(indexed(), samples) == ()


def test_indexed_cost_is_generated_by_corresponding_positions():
    lift = indexed()
    cost = lift.cost((0, 1), (1, 2))
    assert cost == Partition.from_pairs(TRIPLE, [(0, 1), (1, 2)])
    assert cost.blocks() == ((0, 1, 2),)


# === Counterexample 1: quotient-image equality does not preserve meets ===


def quotient_case() -> tuple[QuotientImage, Partition, Partition]:
    """Return the four-element case separating monotone from meet-preserving.

    The objects are the unordered outputs {a, d} and {b, c}. Under ab|cd both
    occupy the same two output classes, and under ac|bd they again occupy the
    same two classes, but under the meet of those regimes, which is discrete,
    they share no member at all.
    """
    members = {"X": frozenset({"a", "d"}), "Y": frozenset({"b", "c"})}
    comparison = QuotientImage(
        output_carrier=OUT,
        objects=("X", "Y"),
        members=lambda x: members[str(x)],
    )
    rho = Partition.from_blocks(OUT, [("a", "b"), ("c", "d")])
    sigma = Partition.from_blocks(OUT, [("a", "c"), ("b", "d")])
    return comparison, rho, sigma


def test_quotient_image_relates_the_objects_under_each_regime_separately():
    comparison, rho, sigma = quotient_case()
    assert comparison.induced(rho).same("X", "Y")
    assert comparison.induced(sigma).same("X", "Y")


def test_quotient_image_separates_them_under_the_meet():
    comparison, rho, sigma = quotient_case()
    assert rho.meet(sigma) == Partition.discrete(OUT)
    assert not comparison.induced(rho.meet(sigma)).same("X", "Y")


def test_quotient_image_fails_meet_preservation():
    comparison, rho, sigma = quotient_case()
    violations = check_meet_preservation(comparison, [rho, sigma])
    assert len(violations) == 1
    assert violations[0].law == "meet-preservation"


def test_quotient_image_is_still_monotone():
    """Meet preservation fails; the order-theoretic property survives."""
    comparison, _, _ = quotient_case()
    samples = list(all_partitions(OUT))
    assert check_monotonicity(comparison, samples) == ()


# === Counterexample 2: optimal matching violates the triangle law ===


def matching_case() -> OptimalMatching:
    """Return the three-object case on which the triangle law fails."""
    members = {
        "X": frozenset({"a", "b"}),
        "Y": frozenset({"a", "c"}),
        "Z": frozenset({"b", "d"}),
    }
    return OptimalMatching(
        output_carrier=OUT,
        objects=("X", "Y", "Z"),
        members=lambda x: members[str(x)],
    )


def test_matching_costs_are_as_computed_by_hand():
    lift = matching_case()
    assert lift.cost("X", "Y") == Partition.from_blocks(OUT, [("b", "c")])
    assert lift.cost("Y", "Z") == Partition.discrete(OUT)
    assert lift.cost("X", "Z") == Partition.from_blocks(OUT, [("a", "d")])


def test_matching_violates_the_triangle_law():
    lift = matching_case()
    direct = lift.cost("X", "Z")
    detour = lift.cost("X", "Y").join(lift.cost("Y", "Z"))
    assert not direct.refines(detour)

    violations = check_lifting_laws(lift)
    assert any(v.law == "triangle" for v in violations)
    assert not any(v.law in {"identity", "symmetry"} for v in violations)


def test_matching_triangle_witness_is_the_expected_triple():
    lift = matching_case()
    triangles = [v for v in check_lifting_laws(lift) if v.law == "triangle"]
    assert ("X", "Y", "Z") in {v.witness for v in triangles}


# === The price of the repair ===


def test_canonicalization_costs_more_than_the_best_matching():
    """Fixing the index before the regime is known can only demand more.

    The two objects {10, 11} and {11, 12} are compared twice over the same
    outputs. Chronological order pairs 10 with 11 and 11 with 12, which
    identifies all three values. The best matching pairs 11 with itself and
    10 with 12, which identifies only those two.
    """
    values = (10, 11, 12)
    members = {"X": frozenset({10, 11}), "Y": frozenset({11, 12})}
    objects = ("X", "Y")

    canonical = IndexedPointwise(
        output_carrier=values,
        objects=objects,
        form=lambda x: cast(tuple[Item, ...], tuple(sorted(members[str(x)]))),
    )
    matching = OptimalMatching(
        output_carrier=values, objects=objects, members=lambda x: members[str(x)]
    )

    canonical_cost = canonical.cost("X", "Y")
    matching_cost = matching.cost("X", "Y")

    assert canonical_cost == Partition.indiscrete(values)
    assert matching_cost == Partition.from_blocks(values, [(10, 12)])

    assert matching_cost.refines(canonical_cost)
    assert not canonical_cost.refines(matching_cost)

    # And the canonicalized comparison is a genuine lifting despite the price.
    assert check_lifting_laws(canonical) == ()
