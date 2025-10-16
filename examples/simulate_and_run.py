import math
from typing import List, Tuple

import pandas as pd

from didimpute import DidImputation


def build_panel() -> pd.DataFrame:
    """Construct a minimal staggered-adoption panel for demonstration."""

    rows: List[Tuple[int, int, float, float]] = []
    for i in range(12):
        Ei = 3.0 if i < 6 else math.nan
        for t in range(6):
            effect = 0.5 if (not math.isnan(Ei) and t >= Ei) else 0.0
            rows.append((i, t, Ei, effect))
    return pd.DataFrame(rows, columns=["i", "t", "Ei", "Y"])


def main() -> None:
    df = build_panel()
    estimator = DidImputation(y="Y", id="i", time="t", Ei="Ei", horizons=(-2, 3), minN=1)
    result = estimator.fit(df)
    print(result.summary())
    print("Pretrend:", result.meta["pretrend"])


if __name__ == "__main__":
    main()
