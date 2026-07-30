import pandas as pd


class FeatureExtractor:
    """
    Extracts AI features from market data.
    """

    @staticmethod
    def extract(df: pd.DataFrame) -> dict:

        last = df.iloc[-1]

        return {
            "close": float(last["close"]),
            "ema_fast": float(last["ema_fast"]),
            "ema_slow": float(last["ema_slow"]),
            "rsi": float(last["rsi"]),
            "atr": float(last["atr"]),
            "macd": float(last["macd"]),
            "macd_signal": float(last["macd_signal"]),
            "macd_histogram": float(last["macd_histogram"]),
        }