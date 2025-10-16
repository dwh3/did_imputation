from __future__ import annotations

import builtins
import importlib
import os
from typing import Tuple

import pandas as pd
import pytest

from didimpute import DidImputation, EstimationError, Result, ValidationError

os.environ.setdefault("MPLBACKEND", "Agg")


def _base_panel() -> pd.DataFrame:
    """Return a minimal panel with one treated and one never-treated unit."""

    return pd.DataFrame(
        {
            "Y": [1.0, 2.0, 1.5, 1.6],
            "i": ["treated", "treated", "control", "control"],
            "t": [0, 1, 0, 1],
            "Ei": [1, 1, float("nan"), float("nan")],
        },
    )


def _make_estimator(**overrides: object) -> DidImputation:
    """Helper to construct DidImputation with sensible defaults."""

    params = dict(y="Y", id="i", time="t", Ei="Ei")
    params.update(overrides)
    return DidImputation(**params)  # type: ignore[arg-type]


def test_fit_invalid_horizons() -> None:
    df = _base_panel()
    estimator = _make_estimator(horizons=(2, -1))
    with pytest.raises(ValidationError, match="Invalid horizons"):
        estimator.fit(df)


def test_fit_invalid_weight_scheme() -> None:
    df = _base_panel()
    estimator = _make_estimator(weight_scheme="bogus")
    with pytest.raises(ValidationError, match="weight_scheme must be one of"):
        estimator.fit(df)


def test_fit_minN_must_be_positive() -> None:
    df = _base_panel()
    estimator = _make_estimator(minN=0)
    with pytest.raises(ValidationError, match="minN must be at least one"):
        estimator.fit(df)


def test_fit_errors_on_unseen_unit_ids() -> None:
    df = pd.DataFrame(
        {
            "Y": [0.0, 0.0, 0.0],
            "i": ["treated_only", "control", "control"],
            "t": [0, 0, 1],
            "Ei": [0, float("nan"), float("nan")],
        },
    )
    estimator = _make_estimator()
    with pytest.raises(EstimationError, match="Encountered unseen unit ids"):
        estimator.fit(df)


def test_result_plot_handles_empty_summary() -> None:
    import matplotlib.pyplot as plt

    result = Result(
        config=_make_estimator(),
        summary_df=pd.DataFrame(columns=["k", "estimate", "ci_low", "ci_high"]),
    )
    fig, ax = plt.subplots()
    try:
        returned_ax = result.plot(ax=ax)
        assert returned_ax is ax
        texts = [text.get_text() for text in ax.texts]
        assert "No results" in texts
    finally:
        plt.close(fig)


def test_result_plot_requires_matplotlib(monkeypatch: pytest.MonkeyPatch) -> None:
    result = Result(
        config=_make_estimator(),
        summary_df=pd.DataFrame(columns=["k", "estimate"]),
    )

    real_import = builtins.__import__

    def _fake_import(
        name: str,
        globals: dict | None = None,
        locals: dict | None = None,
        fromlist: Tuple[str, ...] = (),
        level: int = 0,
    ):
        if name == "matplotlib.pyplot":
            raise ModuleNotFoundError("No module named 'matplotlib'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    with pytest.raises(ModuleNotFoundError, match="pip install \"didimpute\\[plot\\]\""):
        result.plot()


def test_result_plot_with_data() -> None:
    import matplotlib.pyplot as plt

    df = _base_panel()
    result = _make_estimator(minN=1, horizons=(0, 1)).fit(df)
    fig, ax = plt.subplots()
    try:
        axis = result.plot(ax=ax)
        assert axis is ax
        assert axis.lines  # event-study curve drawn
    finally:
        plt.close(fig)


def test_absorbing_requires_linearmodels(monkeypatch: pytest.MonkeyPatch) -> None:
    df = _base_panel()
    estimator = _make_estimator(fe="absorbing")
    real_import = importlib.import_module

    def _raise_when_linearmodels(name: str, *args: object, **kwargs: object):
        if name == "linearmodels":
            raise ModuleNotFoundError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", _raise_when_linearmodels)
    with pytest.raises(ModuleNotFoundError, match="linearmodels"):
        estimator.fit(df)


def test_absorbing_not_implemented(monkeypatch: pytest.MonkeyPatch) -> None:
    df = _base_panel()
    estimator = _make_estimator(fe="absorbing")
    monkeypatch.setattr(importlib, "import_module", lambda name: object())
    with pytest.raises(NotImplementedError, match="fe='absorbing'"):
        estimator.fit(df)


def test_fit_sets_random_state(monkeypatch: pytest.MonkeyPatch) -> None:
    df = _base_panel()
    estimator = _make_estimator(random_state=123)
    captured: dict[str, int] = {}
    monkeypatch.setattr("didimpute.api.set_seed", lambda value: captured.setdefault("seed", value))
    estimator.fit(df)
    assert captured["seed"] == 123
