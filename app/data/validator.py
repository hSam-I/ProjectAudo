import pandas as pd

from app.logging.logger import logger


class DataValidator:

    REQUIRED_COLUMNS = (
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    )

    # Enough rows for the slowest indicator used in strategy decisions
    # (ema_slow=50) to warm up with a small buffer - not the full
    # Ichimoku senkou-span lookback (78), which nothing in the
    # decision path actually depends on.
    MINIMUM_ROWS = 60

    @staticmethod
    def validate(df: pd.DataFrame) -> bool:

        if df.empty:

            logger.warning(
                "Market data validation failed: empty dataframe"
            )

            return False

        missing_columns = [
            column
            for column in DataValidator.REQUIRED_COLUMNS
            if column not in df.columns
        ]

        if missing_columns:

            logger.warning(
                "Market data validation failed: "
                f"missing columns {missing_columns}"
            )

            return False

        if df.isnull().sum().sum() > 0:

            logger.warning(
                "Market data validation failed: contains NaN values"
            )

            return False

        if len(df) < DataValidator.MINIMUM_ROWS:

            logger.warning(
                "Market data validation failed: "
                f"only {len(df)} candles, need at least "
                f"{DataValidator.MINIMUM_ROWS} for indicators to warm up"
            )

            return False

        if (df[["open", "high", "low", "close"]] <= 0).any().any():

            logger.warning(
                "Market data validation failed: non-positive OHLC prices"
            )

            return False

        if (df["volume"] < 0).any():

            logger.warning(
                "Market data validation failed: negative volume"
            )

            return False

        if (
            df["high"]
            < df[["open", "close"]].max(axis=1)
        ).any():

            logger.warning(
                "Market data validation failed: "
                "high is below open/close on at least one candle"
            )

            return False

        if (
            df["low"]
            > df[["open", "close"]].min(axis=1)
        ).any():

            logger.warning(
                "Market data validation failed: "
                "low is above open/close on at least one candle"
            )

            return False

        if df["timestamp"].duplicated().any():

            logger.warning(
                "Market data validation failed: duplicate candle timestamps"
            )

            return False

        if not DataValidator._timestamps_are_evenly_spaced(
            df["timestamp"]
        ):

            logger.warning(
                "Market data validation failed: "
                "gap detected in candle timestamps (missing candle)"
            )

            return False

        return True

    @staticmethod
    def _timestamps_are_evenly_spaced(
        timestamps: pd.Series,
    ) -> bool:

        if len(timestamps) < 3:
            return True

        deltas = (
            timestamps
            .sort_values()
            .diff()
            .dropna()
        )

        median_delta = deltas.median()

        if median_delta == pd.Timedelta(0):
            return True

        return bool(
            (deltas <= median_delta * 1.5).all()
        )
