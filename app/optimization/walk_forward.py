import pandas as pd


class WalkForwardAnalyzer:
    """
    Creates rolling train/test windows.
    """

    def __init__(
        self,
        train_size: int,
        test_size: int,
    ):

        self.train_size = train_size
        self.test_size = test_size

    def generate_windows(
        self,
        df: pd.DataFrame,
    ):

        windows = []

        start = 0

        while True:

            train_start = start
            train_end = train_start + self.train_size

            test_end = train_end + self.test_size

            if test_end > len(df):
                break

            train = df.iloc[
                train_start:train_end
            ]

            test = df.iloc[
                train_end:test_end
            ]

            windows.append(
                (
                    train,
                    test,
                )
            )

            start += self.test_size

        return windows