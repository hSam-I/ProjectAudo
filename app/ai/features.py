import pandas as pd

from app.core.indicator_accessor import IndicatorAccessor


class FeatureExtractor:
    """
    Converts the latest market data into
    AI-ready numerical features.
    """

    @staticmethod
    def extract(df: pd.DataFrame) -> dict:

        last = df.iloc[-1]

        return {

            "ema_fast": float(
                IndicatorAccessor.ema_fast(last) or 0
            ),

            "ema_slow": float(
                IndicatorAccessor.ema_slow(last) or 0
            ),

            "rsi": float(
                IndicatorAccessor.rsi(last) or 50
            ),

            "adx": float(
                IndicatorAccessor.adx(last) or 0
            ),

            "macd": float(
                IndicatorAccessor.macd(last) or 0
            ),

            "macd_signal": float(
                IndicatorAccessor.macd_signal(last) or 0
            ),

            "macd_histogram": float(
                IndicatorAccessor.macd_histogram(last) or 0
            ),

            "atr": float(
                IndicatorAccessor.atr(last) or 0
            ),

            "close": float(
                IndicatorAccessor.close(last) or 0
            ),

            "high": float(
                IndicatorAccessor.high(last) or 0
            ),

            "low": float(
                IndicatorAccessor.low(last) or 0
            ),

            "volume": float(
                IndicatorAccessor.volume(last) or 0
            ),
        }