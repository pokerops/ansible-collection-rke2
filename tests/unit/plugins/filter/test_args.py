"""Tests for plugins/filter/args.py."""

import pytest


@pytest.fixture
def ensure_arg(filters):
    return filters["ensure_arg"]


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ([], ["logging-format=json"]),
        (None, ["logging-format=json"]),
        (["bind-address=0.0.0.0"], ["bind-address=0.0.0.0", "logging-format=json"]),
        # a similarly named argument doesn't count as the same one
        (["logging-format-x=1"], ["logging-format-x=1", "logging-format=json"]),
    ],
)
def test_appends_missing_arg(ensure_arg, args, expected):
    assert ensure_arg(args, "logging-format", "json") == expected


@pytest.mark.parametrize(
    "args",
    [
        ["logging-format=text"],
        ["--logging-format=text"],
        ["-logging-format=text"],
        ["bind-address=0.0.0.0", "--logging-format=text"],
    ],
)
def test_keeps_users_own_value(ensure_arg, args):
    assert ensure_arg(args, "logging-format", "json") == args


def test_empty_value_leaves_args_unchanged(ensure_arg):
    assert ensure_arg(["a=1"], "logging-format", "") == ["a=1"]
    assert ensure_arg(None, "logging-format", "") == []


def test_does_not_modify_its_input(ensure_arg):
    args = ["a=1"]
    ensure_arg(args, "logging-format", "json")
    assert args == ["a=1"]
