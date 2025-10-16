import sys

import pandas as pd

from didimpute import DidImputation


def run_py(
    in_csv: str,
    out_csv: str,
    y: str,
    id_col: str,
    t_col: str,
    Ei_col: str,
    kmin: str,
    kmax: str,
    scheme: str,
) -> None:
    df = pd.read_csv(in_csv)
    estimator = DidImputation(
        y=y,
        id=id_col,
        time=t_col,
        Ei=Ei_col,
        horizons=(int(kmin), int(kmax)),
        weight_scheme=scheme,
        minN=1,
    )
    summary = estimator.fit(df).summary()
    summary.to_csv(out_csv, index=False)


if __name__ == "__main__":
    run_py(*sys.argv[1:])
