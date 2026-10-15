"""Scenario A fails during collection because PyYAML is undeclared."""

import yaml


def test_parse_yaml() -> None:
    assert yaml.safe_load("answer: 42") == {"answer": 42}
