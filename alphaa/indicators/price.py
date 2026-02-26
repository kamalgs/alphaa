"""Price-based indicators."""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd


def sma(period: int) -> Callable[[pd.DataFrame], pd.Series]:
    """Simple moving average of close price."""

    def compute(df: pd.DataFrame) -> pd.Series:
        return df["close"].rolling(window=period).mean()

    compute.__name__ = f"sma_{period}"
    return compute


def rolling_high(period: int) -> Callable[[pd.DataFrame], pd.Series]:
    """Rolling maximum of high price."""

    def compute(df: pd.DataFrame) -> pd.Series:
        return df["high"].rolling(window=period).max()

    compute.__name__ = f"high_{period}"
    return compute


def rolling_low(period: int) -> Callable[[pd.DataFrame], pd.Series]:
    """Rolling minimum of low price."""

    def compute(df: pd.DataFrame) -> pd.Series:
        return df["low"].rolling(window=period).min()

    compute.__name__ = f"low_{period}"
    return compute
