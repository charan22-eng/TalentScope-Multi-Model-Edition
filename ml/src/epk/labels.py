"""Authoritative label encoding for TalentScope.

Task framing: Bands are ordered integers 0 < 1 < 2 corresponding to Low < Medium < High.
Never rely on alphabetical class order.
"""

from typing import Iterable, Sequence
import numpy as np
import pandas as pd

BANDS: list[str] = ["Low", "Medium", "High"]
BAND_TO_INT: dict[str, int] = {"Low": 0, "Medium": 1, "High": 2}
INT_TO_BAND: dict[int, str] = {0: "Low", 1: "Medium", 2: "High"}


def encode_bands(bands: Iterable[str]) -> np.ndarray:
    """Encode band strings ('Low', 'Medium', 'High') to ordered integers 0, 1, 2."""
    if isinstance(bands, pd.Series):
        return bands.map(BAND_TO_INT).to_numpy(dtype=int)
    return np.array([BAND_TO_INT[str(b)] for b in bands], dtype=int)


def decode_bands(ints: Sequence[int] | np.ndarray) -> np.ndarray:
    """Decode integer classes (0, 1, 2) back to band strings ('Low', 'Medium', 'High')."""
    return np.array([INT_TO_BAND[int(i)] for i in ints], dtype=object)
