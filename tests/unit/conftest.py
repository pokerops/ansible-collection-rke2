"""Shared fixtures for the collection's unit tests.

Filter plugins are loaded straight from plugins/filter/*.py, the way
Ansible loads them: each file's FilterModule().filters() maps filter names
to functions. A new filter file is picked up without changes here.
"""

import importlib.util
from pathlib import Path

import pytest

FILTER_DIR = Path(__file__).resolve().parents[2] / "plugins" / "filter"


def filter_files():
    return sorted(p for p in FILTER_DIR.glob("*.py") if not p.name.startswith("_"))


def load_module(path):
    spec = importlib.util.spec_from_file_location(f"filter_plugin_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def filter_modules():
    """Each filter plugin file's module, by file name without .py."""
    return {path.stem: load_module(path) for path in filter_files()}


@pytest.fixture(scope="session")
def filters(filter_modules):
    """Every filter the collection defines, by name, as Ansible sees them."""
    found = {}
    for module in filter_modules.values():
        for name, function in module.FilterModule().filters().items():
            assert name not in found, f"filter {name} is defined twice"
            found[name] = function
    return found
