import pandas as pd


class Ichimoku:
    """
    Ichimoku Cloud
    """

    @staticmethod
    def calculate(
        df: pd.DataFrame,
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_period: int = 52,
    ) -> pd.DataFrame:

        high9 = (
            df["high"]
            .rolling(tenkan_period)
            .max()
        )

        low9 = (
            df["low"]
            .rolling(tenkan_period)
            .min()
        )

        df["tenkan_sen"] = (
            high9 + low9
        ) / 2

        high26 = (
            df["high"]
            .rolling(kijun_period)
            .max()
        )

        low26 = (
            df["low"]
            .rolling(kijun_period)
            .min()
        )

        df["kijun_sen"] = (
            high26 + low26
        ) / 2

        df["senkou_span_a"] = (
            (
                df["tenkan_sen"]
                + df["kijun_sen"]
            )
            / 2
        ).shift(kijun_period)

        high52 = (
            df["high"]
            .rolling(senkou_period)
            .max()
        )

        low52 = (
            df["low"]
            .rolling(senkou_period)
            .min()
        )

        df["senkou_span_b"] = (
            (
                high52
                + low52
            )
            / 2
        ).shift(kijun_period)

        df["chikou_span"] = (
            df["close"]
            .shift(-kijun_period)
        )

        return df