import pandas as pd


class MarketFeatures:
    """
    High-level market regime features.
    """

    @staticmethod
    def build(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        df = df.copy()

        # ----------------------------------------
        # Trend Market
        # ----------------------------------------

        df["trend_market"] = (
            (df["adx"] > 25)
            &
            (df["ema_fast"] > df["ema_slow"])
        )

        # ----------------------------------------
        # Bear Trend
        # ----------------------------------------

        df["bear_market"] = (
            (df["adx"] > 25)
            &
            (df["ema_fast"] < df["ema_slow"])
        )

        # ----------------------------------------
        # Sideways Market
        # ----------------------------------------

        df["sideways_market"] = (
            df["adx"] < 20
        )

        # ----------------------------------------
        # High Volatility
        # ----------------------------------------

        df["high_volatility_market"] = (
            df["atr_percent"] > 2
        )

        # ----------------------------------------
        # Low Volatility
        # ----------------------------------------

        df["low_volatility_market"] = (
            df["atr_percent"] < 1
        )

        # ----------------------------------------
        # Breakout
        # ----------------------------------------

        df["breakout"] = (
            df["close"] > df["bb_upper"]
        )

        # ----------------------------------------
        # Breakdown
        # ----------------------------------------

        df["breakdown"] = (
            df["close"] < df["bb_lower"]
        )

        # ----------------------------------------
        # Above Cloud
        # ----------------------------------------

        df["above_cloud"] = (
            df["close"]
            >
            df["senkou_span_a"]
        ) & (
            df["close"]
            >
            df["senkou_span_b"]
        )

        # ----------------------------------------
        # Below Cloud
        # ----------------------------------------

        df["below_cloud"] = (
            df["close"]
            <
            df["senkou_span_a"]
        ) & (
            df["close"]
            <
            df["senkou_span_b"]
        )

        return df