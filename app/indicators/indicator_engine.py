import pandas as pd

from app.indicators.ema import EMA


class IndicatorEngine:
    """
    Builds indicators required
    by a strategy.
    """

    @staticmethod
    def prepare(
        df: pd.DataFrame,
        ema_fast: int = 20,
        ema_slow: int = 50,
    ) -> pd.DataFrame:

        df = df.copy()

        df = EMA.calculate(
            df=df,
            period=ema_fast,
        )

        df = EMA.calculate(
            df=df,
            period=ema_slow,
        )

        df["ema_fast"] = df[f"ema_{ema_fast}"]

        df["ema_slow"] = df[f"ema_{ema_slow}"]

        return df