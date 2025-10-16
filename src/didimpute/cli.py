from __future__ import annotations

from typing import List, Optional, Tuple

import click
import pandas as pd

from .api import DidImputation
from .utils import format_warnings


def _parse_horizons(value: str) -> Tuple[int, int]:
    """
    Parse a ``kmin:kmax`` horizon string into an integer tuple.

    Parameters
    ----------
    value : str
        Horizon specification provided via the CLI.

    Returns
    -------
    tuple[int, int]
        Parsed ``(k_min, k_max)`` values.

    Raises
    ------
    click.BadParameter
        If the string is not of the form ``a:b`` or cannot be cast to integers.
    """

    if ":" not in value:
        raise click.BadParameter("Horizon must be formatted as 'kmin:kmax'.")
    left, right = value.split(":", 1)
    try:
        return (int(left.strip()), int(right.strip()))
    except ValueError as exc:
        raise click.BadParameter("Horizon bounds must be integers.") from exc


@click.command()
@click.option(
    "--csv",
    "csv_path",
    required=True,
    type=click.Path(exists=True),
    help="Input CSV path.",
)
@click.option("--y", "y_col", required=True, help="Outcome column name.")
@click.option("--id", "id_col", required=True, help="Unit identifier column.")
@click.option(
    "--time",
    "time_col",
    required=True,
    help="Time column (integer-castable).",
)
@click.option(
    "--Ei",
    "Ei_col",
    required=True,
    help="Adoption time column (NaN => never-treated).",
)
@click.option(
    "--controls",
    default="",
    help="Comma-separated control columns, e.g., X1,X2.",
)
@click.option("--weight", default=None, help="Optional non-negative weight column.")
@click.option(
    "--cluster",
    default=None,
    help="Optional cluster-id column; defaults to --id.",
)
@click.option(
    "--horizons",
    default="-5:10",
    help="Event-time range formatted as 'kmin:kmax'.",
)
@click.option(
    "--scheme",
    "scheme",
    default="nobs",
    type=click.Choice(["nobs", "equal", "cohort_share"]),
    show_default=True,
    help="Aggregation weighting scheme.",
)
@click.option(
    "--pretrends",
    default=5,
    type=int,
    show_default=True,
    help="Number of negative ks for pretrend test.",
)
@click.option(
    "--out",
    "out_csv",
    default="didimpute_summary.csv",
    show_default=True,
    help="Output CSV for summary.",
)
@click.option(
    "--plot",
    "plot_png",
    default=None,
    help="If provided, write event-study plot PNG to this path.",
)
def main(
    csv_path: str,
    y_col: str,
    id_col: str,
    time_col: str,
    Ei_col: str,
    controls: str,
    weight: Optional[str],
    cluster: Optional[str],
    horizons: str,
    scheme: str,
    pretrends: int,
    out_csv: str,
    plot_png: Optional[str],
) -> None:
    """
    Run didimpute from the command line on a CSV dataset.

    The CLI mirrors the Python API, wiring data validation, aggregation, SE computation,
    and pretrend tests. Results are written to the requested CSV; optional plotting emits
    a PNG using the default Matplotlib style.
    """

    df = pd.read_csv(csv_path)
    control_list: Optional[List[str]] = (
        [col.strip() for col in controls.split(",") if col.strip()] if controls else None
    )
    horizons_tuple = _parse_horizons(horizons)

    estimator = DidImputation(
        y=y_col,
        id=id_col,
        time=time_col,
        Ei=Ei_col,
        controls=control_list,
        weight=weight,
        cluster=cluster,
        horizons=horizons_tuple,
        weight_scheme=scheme,
        pretrends=pretrends,
    )

    result = estimator.fit(df)
    summary = result.summary()
    summary.to_csv(out_csv, index=False)

    if plot_png:
        try:
            axis = result.plot()
        except ModuleNotFoundError as exc:
            raise click.ClickException(
                "Plotting requires the optional dependency 'matplotlib'. "
                "Install it via `pip install \"didimpute[plot]\"`."
            ) from exc
        axis.figure.savefig(plot_png, bbox_inches="tight")
        axis.figure.clf()

    panel_warnings = result.meta.get("panel", {}).get("warnings", [])
    warning_block = format_warnings(panel_warnings)
    if warning_block:
        click.echo(warning_block, err=True)

    pretrend_info = result.meta.get("pretrend", {})
    click.echo(f"Wrote {out_csv}. Pretrend: {pretrend_info}")
