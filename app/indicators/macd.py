import pandas as pd


def calculate_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """
    Calculates MACD, Signal and Histogram.
    """

    ema_fast = df["close"].ewm(
        span=fast,
        adjust=False,
    ).mean()

    ema_slow = df["close"].ewm(
        span=slow,
        adjust=False,
    ).mean()

    df["macd"] = ema_fast - ema_slow

    df["macd_signal"] = (
        df["macd"]
        .ewm(span=signal, adjust=False)
        .mean()
    )

    df["macd_histogram"] = (
        df["macd"] - df["macd_signal"]
    )

    return df