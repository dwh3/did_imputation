from __future__ import annotations

import click
import pandas as pd
import pytest
from click.testing import CliRunner

from didimpute.cli import _parse_horizons
from didimpute.cli import main as cli_main


def _make_panel() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Y": [1.0, 1.2, 0.9, 1.1],
            "i": ["treated", "treated", "control", "control"],
            "t": [0, 1, 0, 1],
            "Ei": [1, 1, float("nan"), float("nan")],
        },
    )


def test_parse_horizons_validation() -> None:
    """Invalid horizon formats should raise click.BadParameter."""

    with pytest.raises(click.BadParameter):
        _parse_horizons("badformat")
    with pytest.raises(click.BadParameter):
        _parse_horizons("a:b")
    assert _parse_horizons("-2:3") == (-2, 3)


def test_cli_runs_and_writes_outputs(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """End-to-end CLI invocation should emit summary and optional plot."""

    panel = _make_panel()
    csv_path = tmp_path / "panel.csv"
    out_csv = tmp_path / "summary.csv"
    out_plot = tmp_path / "event.png"
    panel.to_csv(csv_path, index=False)

    class _DummyAxis:
        class _Figure:
            def savefig(self, path, **kwargs):
                with open(path, "wb") as handle:
                    handle.write(b"plot")

            def clf(self) -> None:
                return None

        def __init__(self) -> None:
            self.figure = self._Figure()

    def _fake_plot(self, ax=None):
        return _DummyAxis()

    monkeypatch.setattr("didimpute.api.Result.plot", _fake_plot)

    runner = CliRunner()
    result = runner.invoke(
        cli_main,
        [
            "--csv",
            str(csv_path),
            "--y",
            "Y",
            "--id",
            "i",
            "--time",
            "t",
            "--Ei",
            "Ei",
            "--horizons",
            "-1:1",
            "--out",
            str(out_csv),
            "--plot",
            str(out_plot),
        ],
    )

    assert result.exit_code == 0, result.output
    summary = pd.read_csv(out_csv)
    assert "estimate" in summary.columns
    assert out_plot.exists()
