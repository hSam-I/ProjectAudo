from app.indicators.ema import EMA
from app.indicators.rsi import RSI
from app.indicators.atr import ATR
from app.indicators.macd import MACD


class FeaturePipeline:
    """
    Builds every feature required
    by strategies and AI models.
    """

    @staticmethod
    def build(
        df,
        ema_fast: int = 20,
        ema_slow: int = 50,
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

        df = RSI.calculate(df)

        df = ATR.calculate(df)

        df = MACD.calculate(df)

        return df