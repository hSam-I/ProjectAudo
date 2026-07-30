import pandas as pd

from app.core.indicator_accessor import IndicatorAccessor


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

        ema_fast = IndicatorAccessor.ema_fast(last)
        ema_slow = IndicatorAccessor.ema_slow(last)

        if ema_fast is None or ema_slow is None:
            return MarketRegime.RANGE

        ema_fast = float(ema_fast)
        ema_slow = float(ema_slow)

        if ema_slow == 0:
            return MarketRegime.RANGE

        distance = abs(ema_fast - ema_slow)
        percentage = distance / ema_slow * 100

        if percentage >= 3:
            return MarketRegime.TREND

        if percentage <= 1:
            return MarketRegime.RANGE

        return MarketRegime.BREAKOUT