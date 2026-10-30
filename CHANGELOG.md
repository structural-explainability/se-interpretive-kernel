# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on **[Keep a Changelog](https://keepachangelog.com/en/1.1.0/)**
and this project adheres to **[Semantic Versioning](https://semver.org/spec/v2.0.0.html)**.

---

## [Unreleased]

---

## [0.1.0] - 2026-10-30

### Added

- Added the initial Python package, the executable companion to the Lean
  library `se-theory-interpretive-kernel`.
- Added the finite partition algebra and the comparison lifting protocol with
  the three cost laws and their validators.
- Added the finite artifact: frames, outputs, probes, and a total
  interpretation table.
- Added the interpretation-induced kernel, coherence, the generated occurrence
  regime, and the interpretive threshold.
- Added finite incompatibility witnesses and pairwise interpretive demand with
  the generalized ultrametric laws.
- Added an independent pair-set oracle for the partition-based
  implementation.
- Added finite cases mirroring the Lean examples.
- Added exhaustive law checks over every probe family and every pair of
  regimes, and seeded random artifacts, run by the command-line interface.
- Added documentation, CI, release automation, and the repository manifest.

---

## Notes on Versioning and Releases

- We use **SemVer**:
  - **MAJOR** - breaking changes
  - **MINOR** - backward-compatible features
  - **PATCH** - fixes, documentation, tests, tooling
- Versions are driven by git tags. Tag `vX.Y.Z` to release.
- Docs are deployed per version tag and aliased to **latest**.

## Release Procedure (Required)

Follow these steps exactly when creating a new release.

### Task 1. Update release metadata (manual edits)

1.1. `CITATION.cff` - update `version` and `date-released`
1.2. `CHANGELOG.md` - add section, move unreleased entries, update links
1.3. `pyproject.toml` - update build system `fallback-version`
1.4. `codemeta.json` - update `version` and `datePublished`

### Task 2. Validate

```pwsh
.\sit.ps1

uvx gha-tools autoupdate --pin=all --write .github/workflows

uvx zizmor@latest .github/
# suppressed and informational are okay

uvx cffconvert --validate
uvx se-manifest-schema validate-manifest --strict

uv run se-interpretive-kernel --random 2000 --seed 0

uv run python -c "import shutil; from pathlib import Path; shutil.rmtree(Path('dist'), ignore_errors=True)"

uv build
uvx twine check --strict dist/*

uv run python -c "import pathlib, zipfile; wheels=list(pathlib.Path('dist').glob('*.whl')); assert wheels, 'No wheel found'; wheel=wheels[-1]; names=zipfile.ZipFile(wheel).namelist(); packaged=[n for n in names if n.startswith('se_interpretive_kernel/')]; print(packaged); assert packaged, 'Package files missing from wheel'"
```

### Task 3. Commit, push, tag

```shell
git add -A
git commit -m "Prepare X.Y.Z"
git push -u origin main
```

Verify actions run on GitHub. After success:

```shell
git tag vX.Y.Z -m "X.Y.Z"
git push origin vX.Y.Z
```

### Task 4. Verify the Release and Zenodo archive

The release workflow creates a GitHub Release automatically.
To verify:

```shell
gh release view vX.Y.Z                    # confirm Release exists with notes + artifacts
gh run list --workflow=release-pypi.yml   # confirm the workflow succeeded
```

Confirm Zenodo shows a new version-specific DOI for this release
and that it remains linked under the
repository's concept DOI recorded in `CITATION.cff`.

## Only As Needed (delete a tag)

```shell
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z
```

## Links

[Unreleased]: https://github.com/structural-explainability/se-interpretive-kernel/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/structural-explainability/se-interpretive-kernel/releases/tag/v0.1.0

<!-- markdownlint-enable MD024 -->
