"""Scenario D checks the same implementation with correct expectations."""

import pytest

from ci_demo.arithmetic import add


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [(2, 2, 4), (0, 0, 0), (-3, 3, 0), (-2, -5, -7)],
)
def test_addition(left: int, right: int, expected: int) -> None:
    assert add(left, right) == expected
