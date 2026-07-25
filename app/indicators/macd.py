import pandas as pd


class MACD:

    @staticmethod
    def calculate(df: pd.DataFrame, column: str = "close") -> pd.DataFrame:

        ema12 = df[column].ewm(span=12, adjust=False).mean()
        ema26 = df[column].ewm(span=26, adjust=False).mean()

        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_histogram"] = df["macd"] - df["macd_signal"]

        return df