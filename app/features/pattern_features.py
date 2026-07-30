import pandas as pd


class PatternFeatures:
    """
    Candlestick and price action features.
    """

    @staticmethod
    def build(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        df = df.copy()

        # ----------------------------------------
        # Candle Body
        # ----------------------------------------

        df["body"] = (
            df["close"] - df["open"]
        ).abs()

        # ----------------------------------------
        # Candle Range
        # ----------------------------------------

        df["range"] = (
            df["high"] - df["low"]
        )

        # ----------------------------------------
        # Upper Shadow
        # ----------------------------------------

        df["upper_shadow"] = (
            df["high"]
            - df[["open", "close"]].max(axis=1)
        )

        # ----------------------------------------
        # Lower Shadow
        # ----------------------------------------

        df["lower_shadow"] = (
            df[["open", "close"]].min(axis=1)
            - df["low"]
        )

        # ----------------------------------------
        # Body Ratio
        # ----------------------------------------

        df["body_ratio"] = (
            df["body"]
            / df["range"].replace(0, 1)
        )

        # ----------------------------------------
        # Doji
        # ----------------------------------------

        df["doji"] = (
            df["body_ratio"] < 0.1
        )

        # ----------------------------------------
        # Bull Candle
        # ----------------------------------------

        df["bull_candle"] = (
            df["close"] > df["open"]
        )

        # ----------------------------------------
        # Bear Candle
        # ----------------------------------------

        df["bear_candle"] = (
            df["close"] < df["open"]
        )

        # ----------------------------------------
        # Long Upper Wick
        # ----------------------------------------

        df["long_upper_wick"] = (
            df["upper_shadow"]
            >
            df["body"] * 2
        )

        # ----------------------------------------
        # Long Lower Wick
        # ----------------------------------------

        df["long_lower_wick"] = (
            df["lower_shadow"]
            >
            df["body"] * 2
        )

        # ----------------------------------------
        # Hammer
        # ----------------------------------------

        df["hammer"] = (
            df["long_lower_wick"]
            &
            (
                df["upper_shadow"]
                <
                df["body"]
            )
        )

        # ----------------------------------------
        # Shooting Star
        # ----------------------------------------

        df["shooting_star"] = (
            df["long_upper_wick"]
            &
            (
                df["lower_shadow"]
                <
                df["body"]
            )
        )

        return df