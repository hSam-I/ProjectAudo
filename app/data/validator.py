import pandas as pd


class DataValidator:

    @staticmethod
    def validate(df: pd.DataFrame) -> bool:

        if df.empty:
            return False

        if df.isnull().sum().sum() > 0:
            return False

        if not DataValidator._has_no_gaps(df):
            return False

        return True

    @staticmethod
    def _has_no_gaps(df: pd.DataFrame) -> bool:
        """
        Detects missing candles: every gap between consecutive
        timestamps should match the series' own (modal) interval.
        A gap that is e.g. 2x the normal interval means a candle
        is missing from the exchange response.
        """

        if "timestamp" not in df.columns or len(df) < 3:
            return True

        gaps = df["timestamp"].diff().dropna()

        if gaps.empty:
            return True

        expected_gap = gaps.mode().iloc[0]

        return bool((gaps == expected_gap).all())