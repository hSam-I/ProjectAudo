import pandas as pd


class OBV:
    """
    On Balance Volume (OBV)

    Measures buying/selling pressure using volume.
    """

    @staticmethod
    def calculate(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        df = df.copy()

        obv = [0]

        for i in range(1, len(df)):

            if df["close"].iloc[i] > df["close"].iloc[i - 1]:
                obv.append(
                    obv[-1] + df["volume"].iloc[i]
                )

            elif df["close"].iloc[i] < df["close"].iloc[i - 1]:
                obv.append(
                    obv[-1] - df["volume"].iloc[i]
                )

            else:
                obv.append(
                    obv[-1]
                )

        df["obv"] = obv

        return df