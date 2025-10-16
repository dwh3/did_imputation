from __future__ import annotations

import pandas as pd

from didimpute import DidImputation


def test_import_and_fit_skeleton() -> None:
    """Smoke-test the public API on a minimal but valid dataset."""

    model = DidImputation(y="y", id="i", time="t", Ei="Ei")
    frame = pd.DataFrame(
        {
            "y": [0.0, 0.0, 1.0, 1.0],
            "i": [1, 1, 2, 2],
            "t": [0, 1, 0, 1],
            "Ei": [float("nan"), float("nan"), 1.0, 1.0],
        },
    )
    result = model.fit(frame)
    assert hasattr(result, "summary")
