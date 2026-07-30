import pandas as pd


class TrendFeatures:

    @staticmethod
    def build(df: pd.DataFrame) -> pd.DataFrame:

        df = df.copy()

        df["trend_up"] = (
            df["ema_fast"] > df["ema_slow"]
        )

        df["trend_strength"] = (
            (
                df["ema_fast"]
                - df["ema_slow"]
            )
            / df["close"]
        )

        df["strong_trend"] = (
            df["adx"] > 25
        )

        return df