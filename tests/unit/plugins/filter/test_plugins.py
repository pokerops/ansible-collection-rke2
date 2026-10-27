"""Checks every filter plugin file must pass."""

import yaml


def test_filter_plugins_exist(filter_modules):
    assert filter_modules, "no filter plugins found under plugins/filter"


def test_every_plugin_registers_filters(filter_modules):
    for name, module in filter_modules.items():
        registered = module.FilterModule().filters()
        assert registered, f"{name}.py registers no filters"
        for filter_name, function in registered.items():
            assert callable(function), f"{name}.py: {filter_name} is not callable"


def test_every_plugin_is_documented(filter_modules):
    # ansible-doc reads these; DOCUMENTATION must name the filter it documents
    for name, module in filter_modules.items():
        for block in ("DOCUMENTATION", "EXAMPLES", "RETURN"):
            assert getattr(module, block, None), f"{name}.py has no {block}"
        doc = yaml.safe_load(module.DOCUMENTATION)
        assert doc["name"] in module.FilterModule().filters(), (
            f"{name}.py documents {doc['name']}, which it doesn't register"
        )
