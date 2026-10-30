"""Run the Interpretive Kernel law checks under pytest."""

from se_interpretive_kernel.cases import all_cases
from se_interpretive_kernel.check import check_artifact, check_cases, main


def test_cases_satisfy_laws() -> None:
    for artifact in all_cases():
        assert check_artifact(artifact) == []


def test_example_phenomena() -> None:
    assert check_cases() == []


def test_main_runs_clean() -> None:
    assert main(["--random", "10", "--seed", "1"]) == 0
