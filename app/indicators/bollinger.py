import pandas as pd


class BollingerBands:
    """
    Bollinger Bands
    """

    @staticmethod
    def calculate(
        df: pd.DataFrame,
        period: int = 20,
        std_multiplier: float = 2.0,
        column: str = "close",
    ) -> pd.DataFrame:

        sma = (
            df[column]
            .rolling(period)
            .mean()
        )

        std = (
            df[column]
            .rolling(period)
            .std()
        )

        df["bb_middle"] = sma
        df["bb_upper"] = sma + std_multiplier * std
        df["bb_lower"] = sma - std_multiplier * std

        return df