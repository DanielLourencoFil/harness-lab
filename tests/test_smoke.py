"""Smoke test for the empty scaffold: the package imports and the gate can run.

Replaced by real tests as the instrument grows; it exists so that `verify` on the
empty scaffold is a genuine green, not a vacuous one.
"""

import harness_lab


def test_package_exposes_a_version() -> None:
    assert harness_lab.__version__ == "0.1.0"
