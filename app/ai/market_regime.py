import pandas as pd


class MarketRegime:
    """
    Detects current market regime.

    Possible regimes:

    TREND
    RANGE
    BREAKOUT
    """

    TREND = "TREND"
    RANGE = "RANGE"
    BREAKOUT = "BREAKOUT"

    @staticmethod
    def detect(df: pd.DataFrame) -> str:
        """
        Detect market regime using EMA distance.

        Trend:
            EMA distance >= 3%

        Range:
            EMA distance <= 1%

        Otherwise:
            Breakout
        """

        last = df.iloc[-1]

        ema20 = float(last["ema_20"])
        ema50 = float(last["ema_50"])

        distance = abs(ema20 - ema50)

        percentage = distance / ema50 * 100

        if percentage >= 3:
            return MarketRegime.TREND

        if percentage <= 1:
            return MarketRegime.RANGE

        return MarketRegime.BREAKOUT