import pandas as pd


class Stochastic:
    """
    Stochastic Oscillator

    %K and %D
    """

    @staticmethod
    def calculate(
        df: pd.DataFrame,
        period: int = 14,
        smooth: int = 3,
    ) -> pd.DataFrame:

        lowest_low = (
            df["low"]
            .rolling(period)
            .min()
        )

        highest_high = (
            df["high"]
            .rolling(period)
            .max()
        )

        df["stoch_k"] = (
            (
                df["close"] - lowest_low
            )
            /
            (
                highest_high - lowest_low
            )
        ) * 100

        df["stoch_d"] = (
            df["stoch_k"]
            .rolling(smooth)
            .mean()
        )

        return df