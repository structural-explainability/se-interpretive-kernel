"""check.py - Exhaustive and randomized checks of the Interpretive Kernel laws.

Replaces the SE-210 check. Verifies, on finite artifacts, the statements that
the Lean development proves in general:

- the Galois adjunction  L_Q(phi) <= rho  iff  phi <= K_Q(rho),
- unit, counit, and the identities L K L = L and K L K = K,
- monotonicity in the regimes and in the probe family,
- K preserves meets and L preserves joins,
- probe-union duality and the empty family,
- generating-set reduction,
- agreement of the partition-based code with the literal pair-set oracle,
- witnesses, thresholds, and pairwise demand,
- the specific phenomena of Examples A to I.

For each artifact, every selected family Q, every phi on the frames, and every
rho on the outputs is enumerated. This is evidence for small carriers, not a
proof. The proofs are in the Lean library.

Usage::

    python -m se_interpretive_kernel.check [--random N] [--seed S]

Exits nonzero if any check fails.
"""

import argparse
from collections.abc import Sequence
from itertools import combinations
import sys

from .artifact import Artifact
from .cases import (
    all_cases,
    example_a,
    example_b,
    example_c,
    example_d,
    example_e,
    example_f,
    example_g,
    example_h,
    example_i,
    merge,
)
from .demand import demand, kernel_from_demand, ultrametric_violations
from .generated import generated, generated_all_pairs, threshold
from .kernel import coherent, kernel
from .literal import generated_pairs, generator_pairs, kernel_pairs, pairs_of
from .partition import Item, Partition, all_partitions
from .sampling import random_artifacts
from .witness import find_witness, witness_is_valid


def probe_families(artifact: Artifact) -> list[tuple[Item, ...]]:
    """Return every subset of the probes, smallest first, in probe order."""
    subsets: list[tuple[Item, ...]] = []
    for size in range(len(artifact.probes) + 1):
        subsets.extend(combinations(artifact.probes, size))
    return subsets


def check_artifact(artifact: Artifact) -> list[str]:
    """Return a description of every law violated on this artifact."""
    failures: list[str] = []
    name = artifact.label or "artifact"

    def fail(law: str, detail: str = "") -> None:
        failures.append(f"{name}: {law} {detail}".rstrip())

    frame_regimes = list(all_partitions(artifact.frames))
    output_regimes = list(all_partitions(artifact.outputs))
    frame_top = Partition.indiscrete(artifact.frames)
    output_bottom = Partition.discrete(artifact.outputs)
    output_top = Partition.indiscrete(artifact.outputs)
    frame_bottom = Partition.discrete(artifact.frames)
    families = probe_families(artifact)

    for q in families:
        # Totals and bottoms.
        if kernel(artifact, q, output_top) != frame_top:
            fail("K(total) = total", f"Q={q}")
        if generated(artifact, q, frame_bottom) != output_bottom:
            fail("L(discrete) = discrete", f"Q={q}")

        for phi in frame_regimes:
            lift = generated(artifact, q, phi)
            if lift != generated_all_pairs(artifact, q, phi):
                fail("generating-set reduction", f"Q={q} phi={phi.labels}")
            if pairs_of(lift) != generated_pairs(artifact, q, pairs_of(phi)):
                fail("L matches literal oracle", f"Q={q} phi={phi.labels}")
            if not phi.refines(kernel(artifact, q, lift)):
                fail("unit", f"Q={q} phi={phi.labels}")
            if generated(artifact, q, kernel(artifact, q, lift)) != lift:
                fail("L K L = L", f"Q={q} phi={phi.labels}")
            if threshold(artifact, q, phi) != lift:
                fail("threshold = L", f"Q={q} phi={phi.labels}")

        for rho in output_regimes:
            ker = kernel(artifact, q, rho)
            if pairs_of(ker) != kernel_pairs(artifact, q, pairs_of(rho)):
                fail("K matches literal oracle", f"Q={q} rho={rho.labels}")
            if not generated(artifact, q, ker).refines(rho):
                fail("counit", f"Q={q} rho={rho.labels}")
            if kernel(artifact, q, generated(artifact, q, ker)) != ker:
                fail("K L K = K", f"Q={q} rho={rho.labels}")
            if kernel_from_demand(artifact, q, rho) != ker:
                fail("kernel via demand", f"Q={q} rho={rho.labels}")

            for x in artifact.frames:
                for y in artifact.frames:
                    if ker.same(x, y) != demand(artifact, q, x, y).refines(rho):
                        fail("K iff demand refines rho", f"Q={q} rho={rho.labels}")

            for phi in frame_regimes:
                adjoint_left = generated(artifact, q, phi).refines(rho)
                adjoint_right = phi.refines(ker)
                if adjoint_left != adjoint_right:
                    fail("adjunction", f"Q={q} phi={phi.labels} rho={rho.labels}")
                witness = find_witness(artifact, q, phi, rho)
                if adjoint_right != (witness is None):
                    fail(
                        "witness iff incoherent",
                        f"Q={q} phi={phi.labels} rho={rho.labels}",
                    )
                if witness is not None and not witness_is_valid(
                    artifact, q, phi, rho, witness
                ):
                    fail("witness is valid", f"Q={q} phi={phi.labels} rho={rho.labels}")
                if coherent(artifact, q, phi, rho) != adjoint_right:
                    fail("coherent agrees with refinement")

        # Monotonicity and preservation.
        for r1 in output_regimes:
            for r2 in output_regimes:
                k1, k2 = kernel(artifact, q, r1), kernel(artifact, q, r2)
                if r1.refines(r2) and not k1.refines(k2):
                    fail("K monotone")
                if kernel(artifact, q, r1.meet(r2)) != k1.meet(k2):
                    fail("K preserves meets", f"Q={q}")
        for p1 in frame_regimes:
            for p2 in frame_regimes:
                l1, l2 = generated(artifact, q, p1), generated(artifact, q, p2)
                if p1.refines(p2) and not l1.refines(l2):
                    fail("L monotone")
                if generated(artifact, q, p1.join(p2)) != l1.join(l2):
                    fail("L preserves joins", f"Q={q}")

    # Probe-family laws.
    for q1 in families:
        for q2 in families:
            union = tuple(p for p in artifact.probes if p in q1 or p in q2)
            if set(q1) <= set(q2):
                for rho in output_regimes:
                    if not kernel(artifact, q2, rho).refines(kernel(artifact, q1, rho)):
                        fail("more probes refine K", f"{q1} <= {q2}")
                for phi in frame_regimes:
                    if not generated(artifact, q1, phi).refines(
                        generated(artifact, q2, phi)
                    ):
                        fail("more probes enlarge L", f"{q1} <= {q2}")
            for rho in output_regimes:
                if kernel(artifact, union, rho) != kernel(artifact, q1, rho).meet(
                    kernel(artifact, q2, rho)
                ):
                    fail("K probe-union duality", f"{q1} {q2}")
            for phi in frame_regimes:
                if generated(artifact, union, phi) != generated(artifact, q1, phi).join(
                    generated(artifact, q2, phi)
                ):
                    fail("L probe-union duality", f"{q1} {q2}")

    for q in families:
        for violation in ultrametric_violations(artifact, q):
            fail("ultrametric", f"Q={q} {violation}")
    return failures


def check_cases() -> list[str]:
    """Return failures of the specific phenomena of Examples A to I."""
    failures: list[str] = []

    def expect(condition: bool, message: str) -> None:
        if not condition:
            failures.append(f"case: {message}")

    # A: parity regime is coherent with equality on the outputs.
    a = example_a()
    parity = Partition.from_labels(a.frames, {0: 0, 1: 1, 2: 0, 3: 1})
    eq_out = Partition.discrete(a.outputs)
    expect(coherent(a, a.probes, parity, eq_out), "A coherent")
    expect(generated(a, a.probes, parity).refines(eq_out), "A lift finer than equality")

    # B: the total frame regime is incoherent with equality; the witness is valid.
    b = example_b()
    b_total, b_eq = Partition.indiscrete(b.frames), Partition.discrete(b.outputs)
    expect(not coherent(b, b.probes, b_total, b_eq), "B incoherent")
    w = find_witness(b, b.probes, b_total, b_eq)
    expect(
        w is not None and witness_is_valid(b, b.probes, b_total, b_eq, w), "B witness"
    )
    expect(generated(b, b.probes, b_total).same(0, 1), "B lift relates 0 and 1")

    # C: the kernel separates 0 from 1 and relates 1 and 2; the unit is strict.
    c = example_c()
    c_eq = Partition.discrete(c.outputs)
    ker_c = kernel(c, c.probes, c_eq)
    expect(ker_c.same(1, 2) and not ker_c.same(0, 1), "C kernel collapses 1 and 2")
    c_frames_eq = Partition.discrete(c.frames)
    expect(
        c_frames_eq != kernel(c, c.probes, generated(c, c.probes, c_frames_eq)),
        "C unit strict",
    )

    # D: more probes refine the kernel and enlarge the lift, both strictly.
    d = example_d()
    d_eq, d_total = Partition.discrete(d.outputs), Partition.indiscrete(d.frames)
    expect(kernel(d, (0,), d_eq).same(0, 1), "D Q0 does not separate")
    expect(not kernel(d, (0, 1), d_eq).same(0, 1), "D Q1 separates")
    expect(coherent(d, (0,), d_total, d_eq), "D coherent at Q0")
    expect(not coherent(d, (0, 1), d_total, d_eq), "D incoherent at Q1")
    expect(not generated(d, (0,), d_total).same(0, 1), "D L_Q0 stays discrete")
    expect(generated(d, (0, 1), d_total).same(0, 1), "D L_Q1 relates 0 and 1")

    # E: the generating pairs are not transitive; the closure relates 0 and 2.
    e = example_e()
    e_total = Partition.indiscrete(e.frames)
    expect(generated(e, e.probes, e_total).same(0, 2), "E closure relates 0 and 2")
    expect(
        (0, 2) not in generator_pairs(e, e.probes, pairs_of(e_total)),
        "E generators skip (0, 2)",
    )

    # F: the counit is strict.
    f = example_f()
    f_total = Partition.indiscrete(f.outputs)
    f_lk = generated(f, f.probes, kernel(f, f.probes, f_total))
    expect(f_lk != f_total and f_lk.refines(f_total), "F counit strict")

    # G: K does not preserve joins.
    g = example_g()
    rho, sigma = merge(g.outputs, 0, 1), merge(g.outputs, 1, 2)
    kg = lambda r: kernel(g, g.probes, r)
    expect(
        kg(rho.join(sigma)) != kg(rho).join(kg(sigma)), "G K does not preserve joins"
    )

    # H: L does not preserve meets.
    h = example_h()
    phi1, phi2 = merge(h.frames, 0, 1), merge(h.frames, 0, 2)
    lh = lambda p: generated(h, h.probes, p)
    expect(
        lh(phi1.meet(phi2)) != lh(phi1).meet(lh(phi2)), "H L does not preserve meets"
    )

    # I: thresholds are incomparable.
    i = example_i()
    t01 = threshold(i, i.probes, merge(i.frames, 0, 1))
    t12 = threshold(i, i.probes, merge(i.frames, 1, 2))
    expect(not t01.refines(t12) and not t12.refines(t01), "I thresholds incomparable")

    # J: without equivalence the adjunction fails (empty family, empty relation).
    # Partition values are always equivalences, so this is stated, not run.
    return failures


def main(argv: Sequence[str] | None = None) -> int:
    """Run all checks and return a process exit status."""
    parser = argparse.ArgumentParser(description="Check Interpretive Kernel laws.")
    parser.add_argument("--random", type=int, default=50, help="random artifacts")
    parser.add_argument("--seed", type=int, default=0, help="random seed")
    args = parser.parse_args(argv)

    failures: list[str] = []
    for artifact in all_cases():
        failures.extend(check_artifact(artifact))
    failures.extend(check_cases())
    checked = len(all_cases())
    for artifact in random_artifacts(args.random, args.seed):
        failures.extend(check_artifact(artifact))
        checked += 1

    for line in failures[:50]:
        print(line)
    status = "FAILED" if failures else "OK"
    print(f"{status}: {checked} artifacts, {len(failures)} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
