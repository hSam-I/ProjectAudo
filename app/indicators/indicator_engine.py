import pandas as pd

from app.indicators.adx import ADX
from app.indicators.atr import ATR
from app.indicators.ema import EMA
from app.indicators.macd import MACD
from app.indicators.rsi import RSI


class IndicatorEngine:
    """
    Builds every indicator required
    by strategies and AI modules.
    """

    @staticmethod
    def prepare(
        df: pd.DataFrame,
        ema_fast: int = 20,
        ema_slow: int = 50,
        rsi_period: int = 14,
        atr_period: int = 14,
        adx_period: int = 14,
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

        df = RSI.calculate(
            df=df,
            period=rsi_period,
        )

        df = ATR.calculate(
            df=df,
            period=atr_period,
        )

        df = MACD.calculate(df)

        df = ADX.calculate(
            df=df,
            period=adx_period,
        )

        return df