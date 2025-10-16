from __future__ import annotations

import random

import numpy as np

from didimpute.utils import format_warnings, set_seed


def test_format_warnings_empty() -> None:
    """Formatting with no warnings should return an empty string."""

    assert format_warnings([]) == ""


def test_format_warnings_non_empty() -> None:
    """Formatting with warnings should include header and newline separation."""

    message = format_warnings(["issue one", "issue two"])
    assert message.startswith("Warnings:\n")
    assert "issue one" in message
    assert "issue two" in message


def test_set_seed_deterministic() -> None:
    """Seeding should produce reproducible Python and NumPy random streams."""

    py_state = random.getstate()
    np_state = np.random.get_state()
    try:
        set_seed(42)
        sample_one = (random.random(), float(np.random.rand()))
        set_seed(42)
        sample_two = (random.random(), float(np.random.rand()))
        assert sample_one == sample_two
    finally:
        random.setstate(py_state)
        np.random.set_state(np_state)
