import pandas as pd


class EMA:

    @staticmethod
    def calculate(
        df: pd.DataFrame,
        period: int,
        column: str = "close",
    ) -> pd.DataFrame:

        df[f"ema_{period}"] = (
            df[column]
            .ewm(span=period, adjust=False)
            .mean()
        )

        return df