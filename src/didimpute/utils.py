from __future__ import annotations

import random
from typing import List, Optional

import numpy as np


def set_seed(seed: Optional[int]) -> None:
    """
    Seed Python and NumPy random number generators for determinism.

    Parameters
    ----------
    seed : int | None
        Value used to seed both RNGs. When ``None`` the function is a no-op.

    Notes
    -----
    The v0.1 estimator is deterministic; this hook keeps later stochastic extensions reproducible.
    """

    if seed is None:
        return
    random.seed(seed)
    np.random.seed(seed)


def format_warnings(warnings: List[str]) -> str:
    """
    Format panel warnings for user-facing output.

    Parameters
    ----------
    warnings : list[str]
        Collection of warning messages gathered during validation.

    Returns
    -------
    str
        ``"Warnings:\\n..."`` when messages exist; otherwise an empty string.
    """

    if not warnings:
        return ""
    return "Warnings:\n" + "\n".join(warnings)
