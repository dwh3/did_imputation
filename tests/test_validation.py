from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from didimpute import ValidationError
from didimpute.validation import validate_and_prepare, validate_config


def test_config_validation() -> None:
    """Basic happy-path and failure scenarios for configuration validation."""

    validate_config((-2, 2), 1, "nobs", 0.95)
    with pytest.raises(ValidationError):
        validate_config((2, -2), 1, "nobs", 0.95)
    with pytest.raises(ValidationError):
        validate_config((-2, 2), 0, "nobs", 0.95)
    with pytest.raises(ValidationError):
        validate_config((-2, 2), 1, "bad", 0.95)
    with pytest.raises(ValidationError):
        validate_config((-2, 2), 1, "nobs", 1.5)


def test_duplicate_detection() -> None:
    """Duplicated (id, time) pairs should trigger a ValidationError."""

    df = pd.DataFrame(
        {"Y": [1, 1], "i": [1, 1], "t": [0, 0], "Ei": [np.nan, np.nan]},
    )
    with pytest.raises(ValidationError):
        validate_and_prepare(df, "Y", "i", "t", "Ei", None, None, None)


def test_untreated_presence_and_types() -> None:
    """Untreated observation count should be positive and helper columns present."""

    df = pd.DataFrame(
        {"Y": [1, 2, 3, 4], "i": [1, 1, 2, 2], "t": [0, 1, 0, 1], "Ei": [1, 1, np.nan, np.nan]},
    )
    ctx = validate_and_prepare(df, "Y", "i", "t", "Ei", None, None, None)
    prepared = ctx["df"]
    assert "_k" in prepared
    assert prepared["_untreated"].sum() > 0


def test_weights_nonnegative() -> None:
    """Negative weights should raise a ValidationError."""

    df = pd.DataFrame(
        {"Y": [1, 2], "i": [1, 2], "t": [0, 1], "Ei": [np.nan, np.nan], "w": [-1.0, 0.5]},
    )
    with pytest.raises(ValidationError):
        validate_and_prepare(df, "Y", "i", "t", "Ei", None, "w", None)
