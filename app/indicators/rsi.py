import pandas as pd


class RSI:

    @staticmethod
    def calculate(
        df: pd.DataFrame,
        period: int = 14,
        column: str = "close",
    ) -> pd.DataFrame:

        delta = df[column].diff()

        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss

        df["rsi"] = 100 - (100 / (1 + rs))

        return df