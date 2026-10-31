"""Check probe sensitivity and explanations against their definitions."""

from itertools import chain

from se_interpretive_kernel.artifact import Artifact
from se_interpretive_kernel.cases import all_cases, example_e
from se_interpretive_kernel.check import probe_families
from se_interpretive_kernel.explain import (
    Step,
    explain,
    explain_threshold,
    format_steps,
    steps_are_valid,
)
from se_interpretive_kernel.generated import generated
from se_interpretive_kernel.kernel import kernel
from se_interpretive_kernel.partition import Partition, all_partitions, join_all
from se_interpretive_kernel.probes import (
    load_bearing_probes,
    minimal_probe_sets,
    probe_contributions,
    sole_separated_pairs,
)
from se_interpretive_kernel.sampling import random_artifacts


def artifacts() -> list[Artifact]:
    """Return the example artifacts followed by seeded random ones."""
    return list(chain(all_cases(), random_artifacts(40, seed=5)))


def test_explain_agrees_with_generated() -> None:
    """A derivation exists exactly when the threshold relates two outputs."""
    for artifact in artifacts():
        for q in probe_families(artifact):
            for phi in all_partitions(artifact.frames):
                threshold = generated(artifact, q, phi)
                for a in artifact.outputs:
                    for b in artifact.outputs:
                        steps = explain(artifact, q, phi, a, b)
                        assert (steps is not None) == threshold.same(a, b)
                        if steps is not None:
                            assert steps_are_valid(artifact, q, phi, a, b, steps)


def test_explain_threshold_covers_every_forced_identification() -> None:
    """Every non-singleton block of the threshold is connected by derivations."""
    for artifact in artifacts():
        for q in probe_families(artifact):
            for phi in all_partitions(artifact.frames):
                threshold = generated(artifact, q, phi)
                explanations = explain_threshold(artifact, q, phi)
                forced = sum(len(block) - 1 for block in threshold.blocks())
                assert len(explanations) == forced
                for item in explanations:
                    assert steps_are_valid(
                        artifact, q, phi, item.output_1, item.output_2, item.steps
                    )
                    assert format_steps(item.steps).count("\n") == len(item.steps) - 1


def test_probe_contributions_join_to_threshold() -> None:
    """The threshold is the join of what each probe forces alone."""
    for artifact in artifacts():
        for q in probe_families(artifact):
            for phi in all_partitions(artifact.frames):
                contributions = probe_contributions(artifact, q, phi)
                parts = contributions.values()
                assert join_all(artifact.outputs, parts) == generated(artifact, q, phi)
                for probe, part in contributions.items():
                    assert part == generated(artifact, (probe,), phi)
                    assert part.refines(generated(artifact, q, phi))


def test_steps_are_valid_rejects_tampering() -> None:
    """A derivation that is altered no longer validates."""
    artifact = example_e()
    phi = Partition.indiscrete(artifact.frames)
    q = artifact.probes
    steps = explain(artifact, q, phi, 0, 2)
    assert steps is not None
    assert steps_are_valid(artifact, q, phi, 0, 2, steps)
    first = steps[0]
    wrong_output = Step(first.probe, first.frame_1, first.frame_2, 2, first.output_to)
    assert not steps_are_valid(artifact, q, phi, 0, 2, [wrong_output, *steps[1:]])
    assert not steps_are_valid(artifact, q, phi, 0, 2, steps[:-1])
    assert not steps_are_valid(artifact, q, phi, 2, 0, steps)
    assert not steps_are_valid(artifact, q, phi, 0, 2, [])
    assert not steps_are_valid(artifact, (), phi, 0, 2, steps)
    unrelated = Partition.discrete(artifact.frames)
    assert not steps_are_valid(artifact, q, unrelated, 0, 2, steps)
    broken_chain = [first, first]
    assert steps_are_valid(artifact, q, phi, 0, 1, [first])
    assert not steps_are_valid(artifact, q, phi, 0, 1, broken_chain)


def test_minimal_probe_sets_and_load_bearing_probes() -> None:
    """Minimal sets preserve the kernel; load-bearing probes are in all of them."""
    for artifact in artifacts():
        for q in probe_families(artifact):
            for rho in all_partitions(artifact.outputs):
                target = kernel(artifact, q, rho)
                minimal = minimal_probe_sets(artifact, q, rho)
                assert minimal
                for subset in minimal:
                    assert kernel(artifact, subset, rho) == target
                    for drop in subset:
                        smaller = [p for p in subset if p != drop]
                        assert kernel(artifact, smaller, rho) != target
                bearing = set(load_bearing_probes(artifact, q, rho))
                in_all = set(q)
                for subset in minimal:
                    in_all &= set(subset)
                assert bearing == in_all


def test_sole_separated_pairs_match_removal() -> None:
    """A pair is listed under p exactly when removing p merges it."""
    for artifact in artifacts():
        for q in probe_families(artifact):
            for rho in all_partitions(artifact.outputs):
                full = kernel(artifact, q, rho)
                listed = sole_separated_pairs(artifact, q, rho)
                for probe in q:
                    without = kernel(artifact, [p for p in q if p != probe], rho)
                    expected = [
                        (x, y)
                        for i, x in enumerate(artifact.frames)
                        for y in artifact.frames[i + 1 :]
                        if not full.same(x, y) and without.same(x, y)
                    ]
                    assert listed[probe] == expected
