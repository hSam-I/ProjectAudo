import pandas as pd


class RSI:
    """
    Relative Strength Index (RSI)

    Uses Wilder's smoothing (RMA), which is compatible with
    TradingView and most professional trading platforms.
    """

    @staticmethod
    def calculate(
        df: pd.DataFrame,
        period: int = 14,
        column: str = "close",
    ) -> pd.DataFrame:

        delta = df[column].diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        # Wilder's Moving Average (RMA)
        avg_gain = gain.ewm(
            alpha=1 / period,
            adjust=False,
        ).mean()

        avg_loss = loss.ewm(
            alpha=1 / period,
            adjust=False,
        ).mean()

        rs = avg_gain / avg_loss

        df["rsi"] = 100 - (100 / (1 + rs))

        return df