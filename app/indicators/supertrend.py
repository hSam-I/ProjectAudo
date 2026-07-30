import numpy as np
import pandas as pd

from app.indicators.atr import ATR


class SuperTrend:
    """
    SuperTrend Indicator
    """

    @staticmethod
    def calculate(
        df: pd.DataFrame,
        period: int = 10,
        multiplier: float = 3.0,
    ) -> pd.DataFrame:

        df = ATR.calculate(
            df,
            period=period,
        )

        hl2 = (
            df["high"] + df["low"]
        ) / 2

        upperband = hl2 + (
            multiplier * df["atr"]
        )

        lowerband = hl2 - (
            multiplier * df["atr"]
        )

        supertrend = np.zeros(len(df))
        direction = np.ones(len(df))

        for i in range(1, len(df)):

            if (
                df["close"].iloc[i]
                > upperband.iloc[i - 1]
            ):
                direction[i] = 1

            elif (
                df["close"].iloc[i]
                < lowerband.iloc[i - 1]
            ):
                direction[i] = -1

            else:

                direction[i] = direction[i - 1]

                if (
                    direction[i] > 0
                    and lowerband.iloc[i]
                    < lowerband.iloc[i - 1]
                ):
                    lowerband.iloc[i] = (
                        lowerband.iloc[i - 1]
                    )

                if (
                    direction[i] < 0
                    and upperband.iloc[i]
                    > upperband.iloc[i - 1]
                ):
                    upperband.iloc[i] = (
                        upperband.iloc[i - 1]
                    )

            if direction[i] > 0:
                supertrend[i] = lowerband.iloc[i]
            else:
                supertrend[i] = upperband.iloc[i]

        df["supertrend"] = supertrend
        df["supertrend_direction"] = direction

        return df