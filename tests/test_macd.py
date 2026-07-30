from app.indicators.atr import ATR
from app.indicators.ema import EMA
from app.indicators.macd import MACD
from app.indicators.rsi import RSI


class FeaturePipeline:
    """
    Creates every indicator required by
    strategies, optimizers and AI models.
    """

    @staticmethod
    def build(
        df,
        ema_fast: int = 20,
        ema_slow: int = 50,
        rsi_period: int = 14,
        atr_period: int = 14,
    ):

        df = df.copy()

        df = EMA.calculate(
            df,
            ema_fast,
        )

        df = EMA.calculate(
            df,
            ema_slow,
        )

        df["ema_fast"] = df[f"ema_{ema_fast}"]

        df["ema_slow"] = df[f"ema_{ema_slow}"]

        df = RSI.calculate(
            df,
            rsi_period,
        )

        df = ATR.calculate(
            df,
            atr_period,
        )

        df = MACD.calculate(
            df,
        )

        return df