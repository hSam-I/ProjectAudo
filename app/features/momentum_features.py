import pandas as pd


class MomentumFeatures:
    """
    Momentum related AI features.
    """

    @staticmethod
    def build(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        df = df.copy()

        # RSI Zones

        df["rsi_overbought"] = (
            df["rsi"] >= 70
        )

        df["rsi_oversold"] = (
            df["rsi"] <= 30
        )

        # MACD

        df["macd_positive"] = (
            df["macd"] > 0
        )

        df["macd_bullish"] = (
            df["macd"]
            >
            df["macd_signal"]
        )

        # Histogram

        df["macd_hist_positive"] = (
            df["macd_histogram"] > 0
        )

        return df