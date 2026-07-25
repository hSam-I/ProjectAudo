import pandas as pd


class DataValidator:

    @staticmethod
    def validate(df: pd.DataFrame) -> bool:

        if df.empty:
            return False

        if df.isnull().sum().sum() > 0:
            return False

        return True