"""Filters for building rke2 component argument lists."""

DOCUMENTATION = r"""
name: ensure_arg
short_description: Add a name=value argument unless the list already sets it
description:
  - Returns I(args) with C(name=value) appended, unless an item already sets
    I(name) (with or without leading dashes, e.g. C(--name=...)) or I(value)
    is empty, in which case I(args) is returned unchanged.
options:
  _input:
    description: Component arguments, as rke2's C(*-arg) config options take them.
    type: list
    elements: str
    required: true
  name:
    description: Argument name, without leading dashes.
    type: str
    required: true
  value:
    description: Argument value; empty leaves the list unchanged.
    type: str
    required: true
"""

EXAMPLES = r"""
rke2_kubelet_arg: "{{ rke2_kubelet_arg | default([]) | pokerops.rke2.ensure_arg('logging-format', 'json') }}"
"""

RETURN = r"""
_value:
  description: The arguments, with C(name=value) appended when it was missing.
  type: list
  elements: str
"""


def ensure_arg(args, name, value):
    args = list(args or [])
    if not value or any(str(arg).lstrip("-").startswith(name + "=") for arg in args):
        return args
    return args + [f"{name}={value}"]


class FilterModule:
    def filters(self):
        return {"ensure_arg": ensure_arg}
