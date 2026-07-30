import pandas as pd


class VolatilityFeatures:
    """
    Volatility related AI features.
    """

    @staticmethod
    def build(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        df = df.copy()

        # ATR relative to price

        df["atr_percent"] = (
            df["atr"] / df["close"]
        ) * 100

        # High volatility

        df["high_volatility"] = (
            df["atr_percent"] > 2.0
        )

        # Bollinger Width

        df["bb_width"] = (
            (
                df["bb_upper"]
                - df["bb_lower"]
            )
            / df["bb_middle"]
        )

        # Bollinger Squeeze

        df["bb_squeeze"] = (
            df["bb_width"] < 0.05
        )

        # Bollinger Breakout

        df["bb_breakout_up"] = (
            df["close"] > df["bb_upper"]
        )

        df["bb_breakout_down"] = (
            df["close"] < df["bb_lower"]
        )

        return df