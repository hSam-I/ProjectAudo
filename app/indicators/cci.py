import pandas as pd


class CCI:
    """
    Commodity Channel Index
    """

    @staticmethod
    def calculate(
        df: pd.DataFrame,
        period: int = 20,
    ) -> pd.DataFrame:

        typical_price = (
            df["high"]
            + df["low"]
            + df["close"]
        ) / 3

        sma = (
            typical_price
            .rolling(period)
            .mean()
        )

        mean_deviation = (
            typical_price
            .rolling(period)
            .apply(
                lambda x: (
                    abs(x - x.mean())
                ).mean(),
                raw=False,
            )
        )

        df["cci"] = (
            typical_price - sma
        ) / (
            0.015 * mean_deviation
        )

        return df