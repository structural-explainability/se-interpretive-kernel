# se-interpretive-kernel

[![PyPI](https://img.shields.io/pypi/v/se-interpretive-kernel?logo=pypi&label=pypi)](https://pypi.org/project/se-interpretive-kernel/)
[![Docs Site](https://img.shields.io/badge/docs-site-blue?logo=github)](https://structural-explainability.github.io/se-interpretive-kernel/)
[![Repo](https://img.shields.io/badge/repo-GitHub-black?logo=github)](https://github.com/structural-explainability/se-interpretive-kernel)
[![Python 3.14](https://img.shields.io/badge/python-3.14%2B-blue?logo=python)](./pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](./LICENSE)

[![CI](https://github.com/structural-explainability/se-interpretive-kernel/actions/workflows/ci-python-zensical.yml/badge.svg?branch=main)](https://github.com/structural-explainability/se-interpretive-kernel/actions/workflows/ci-python-zensical.yml)
[![Docs-Deploy](https://github.com/structural-explainability/se-interpretive-kernel/actions/workflows/deploy-zensical.yml/badge.svg?branch=main)](https://github.com/structural-explainability/se-interpretive-kernel/actions/workflows/deploy-zensical.yml)
[![Pre-Release](https://github.com/structural-explainability/se-interpretive-kernel/actions/workflows/pre-release.yml/badge.svg?branch=main)](https://github.com/structural-explainability/se-interpretive-kernel/actions/workflows/pre-release.yml)
[![Release](https://github.com/structural-explainability/se-interpretive-kernel/actions/workflows/release-pypi.yml/badge.svg)](https://github.com/structural-explainability/se-interpretive-kernel/actions/workflows/release-pypi.yml)
[![Links](https://github.com/structural-explainability/se-interpretive-kernel/actions/workflows/links.yml/badge.svg?branch=main)](https://github.com/structural-explainability/se-interpretive-kernel/actions/workflows/links.yml)
[![Dependabot](https://img.shields.io/badge/Dependabot-enabled-brightgreen.svg)](https://github.com/structural-explainability/se-interpretive-kernel/security)

> An executable contract for the Structural Explainability (SE) **interpretive kernel**:
> when a declared identity regime over environments induces well-defined judgments about the
> objects an interpretation produces, and what it costs when it does not.

## Purpose

An interpretation `I` maps a probe and an environment to structured output.
Fix a finite probe domain `P` and an equivalence `rho` on outputs.
The **interpretive kernel** relates two environments when no probe can tell
them apart:

```text
F ~ker F'   iff   for every p in P, I(p, F) is rho-indistinguishable from I(p, F')
```

A declared identity regime over environments induces well-defined
object-level judgments exactly when it refines the kernel, and every failure
comes with a finite witness: the probe and the pair of environments on which
the regime identifies what interpretation separates.

The stronger result is the **threshold**.
For a declared regime `phi`, the least output equivalence under which `phi` is
coherent is generated directly by the pairs `phi` forces together:

```text
L(phi) = equivalence closure of { (I(p, F), I(p, F')) : p in P, F phi F' }
```

`L` is left adjoint to the kernel, so no search over the lattice is required.
The result is a computed commitment rather than a pass or fail verdict:
not
"this regime is inadmissible" but
"this regime is coherent only if you are willing to call these outputs the same".

The construction is domain-agnostic.
Interpretation is supplied by the consuming domain and not imported.

## Status

This is the first slice.

- **`partition.py`**: finite partition algebra over a declared carrier.
  Refinement, meet, join, equivalence closure by union-find, refinement
  witnesses, and exhaustive enumeration for law checking.
  The order is refinement, so finer partitions are lower, the discrete
  partition is bottom, meet is intersection, and join is the closure of the
  union.
- **`lifting.py`**: comparison liftings, the three cost laws, and validators
  for those laws, for meet preservation, and for monotonicity.

The layer boundary is deliberate.
`partition.py` imports nothing else in this package and carries no vocabulary
from the layers above it, so it can be extracted later without a rewrite.
It is not extracted now, because extraction is justified by a second consumer
needing the same public surface and no second consumer exists.

## Comparison Liftings Have Laws

Comparing structured outputs requires carrying an output equivalence up to
the structures:

```text
C : Eq(O) -> Eq(X)
```

The kernel construction needs `C` to preserve arbitrary meets.
Complete meet homomorphisms of this shape are exactly the `Eq(O)`-valued
generalized ultrametrics on `X`, so every one of them is given by a cost
`delta(x, y)`: the least output identification that would make two objects
the same.
The cost must satisfy three laws, and `check_lifting_laws` is the finite test
that decides whether a supplied comparison has them.

Two comparisons in this package are present because they fail, and both
failures are regressions that must keep failing.

| comparison                       | monotone | meet-preserving | is a lifting               |
| -------------------------------- | -------- | --------------- | -------------------------- |
| indexed pointwise                | yes      | yes             | yes                        |
| quotient-image equality          | yes      | **no**          | no                         |
| optimal matching over bijections | -        | -               | **no**, triangle law fails |

Quotient-image equality on unordered outputs is the natural way to compare
occurrence sets and does not preserve meets, so no cost represents it.
Optimal matching is the natural repair and violates the triangle law, because
moving the meet over alternative bijections through the join needs a
distributivity the partition lattice does not have.

The surviving repair is a declared canonicalization, which fixes the index
before the output regime is known.
It restores every law, and it costs something: the identification it demands
is no finer than the best matching would have required.
That price is measured in the test suite rather than asserted.

A canonicalization is therefore a declared artifact, not an implementation
detail.
One that is not injective identifies distinct objects at zero cost, which
declares an identity without ever appearing as a declared identity regime.

## Run

```bash
uv sync --extra dev --extra docs --upgrade

uv run pytest
```

## Developer Command Reference

<details>
<summary>Show command reference</summary>

### In a machine terminal

Open a machine terminal where you want the project:

```shell
git clone https://github.com/structural-explainability/se-interpretive-kernel

cd se-interpretive-kernel
code .
```

### In a VS Code terminal

```shell
uv self update
uv python pin 3.14
uv lock --upgrade
uv sync --extra dev --extra docs --upgrade

uvx pre-commit install
uvx pre-commit autoupdate

git add -A
uvx pre-commit run --all-files
# repeat if changes were made
uvx pre-commit run --all-files

# types, tests, docs
uv run pyright
uv run pytest
uv run zensical build

# save progress
git add -A
git commit -m "update"
git push -u origin main
```

</details>

## Planned

The boundary of the current slice is explicit.

- `outcome.py`: the tagged output domain carrying end, undefined, and error,
  which makes length mismatch a declared comparison result rather than an
  exception.
- `signature.py`: declared roles for each variable. A variable in the probe
  domain is a test condition, in the environment domain it is a thing whose
  sameness is at issue, and in the output domain it is observable. The same
  variable in three positions asks three different questions, so position is
  a declaration and must be validated.
- `kernel.py` and `threshold.py`: `K` and `L` over a supplied interpretation,
  sharing one generating-pair construction so the adjunction round trip is
  not tested against two independent implementations.
- `witness.py`: witness forms for each failure.

## Related Repositories

- [se-theory-interpretive-kernel](https://github.com/structural-explainability/se-theory-interpretive-kernel):
  the Lean formalization of the same results. The two are independent
  realizations of one contract, and disagreement between them means one of
  the definitions is wrong.
- [se-verification-operational-identity](https://github.com/structural-explainability/se-verification-operational-identity):
  SE-210, whose refinement and four-way sibling positioning this construction
  builds on.

## Citation

[CITATION.cff](./CITATION.cff)

## Software Metadata

[CodeMeta (`codemeta.json`)](./codemeta.json)

## License

[MIT](./LICENSE)

## Repository Manifest

[SE_MANIFEST.toml](./SE_MANIFEST.toml)
