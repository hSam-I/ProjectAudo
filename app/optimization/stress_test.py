import pandas as pd


class StressTestEngine:
    """
    Applies different stress scenarios
    to market data.
    """

    def flash_crash(
        self,
        df: pd.DataFrame,
        percent: float = 0.30,
    ) -> pd.DataFrame:

        stressed = df.copy()

        stressed["close"] *= (
            1 - percent
        )

        return stressed

    def rally(
        self,
        df: pd.DataFrame,
        percent: float = 0.20,
    ) -> pd.DataFrame:

        stressed = df.copy()

        stressed["close"] *= (
            1 + percent
        )

        return stressed

    def increase_volatility(
        self,
        df: pd.DataFrame,
        multiplier: float = 2.0,
    ) -> pd.DataFrame:

        stressed = df.copy()

        if "atr" in stressed.columns:

            stressed["atr"] *= multiplier

        return stressed

    def gap_down(
        self,
        df: pd.DataFrame,
        percent: float = 0.10,
    ) -> pd.DataFrame:

        stressed = df.copy()

        stressed.iloc[0, stressed.columns.get_loc("close")] *= (
            1 - percent
        )

        return stressed