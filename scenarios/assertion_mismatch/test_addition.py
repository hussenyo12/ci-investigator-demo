"""Scenario B deliberately contains an incorrect expectation."""

from ci_demo.arithmetic import add


def test_addition() -> None:
    assert add(2, 2) == 5
