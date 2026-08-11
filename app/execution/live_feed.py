import time
from datetime import datetime, timezone

import pandas as pd

from app.config.settings import settings
from app.data.binance_provider import BinanceProvider
from app.logging.logger import logger

_UNIT_SECONDS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
}


def timeframe_to_seconds(timeframe: str) -> int:
    """
    Converts a ccxt-style timeframe string ("1m", "15m", "1h", "4h",
    "1d", "1w") to seconds. Deliberately narrow (no month support,
    ccxt's "1M") since nothing in this codebase's default config uses
    anything coarser than days.
    """

    unit = timeframe[-1]

    if unit not in _UNIT_SECONDS:
        raise ValueError(f"Unsupported timeframe unit: {timeframe!r}")

    amount = int(timeframe[:-1])

    return amount * _UNIT_SECONDS[unit]


def utc_now() -> pd.Timestamp:
    """
    Timezone-naive UTC "now", matching BinanceProvider's
    pd.to_datetime(..., unit="ms") timestamps (also tz-naive UTC).
    """

    return pd.Timestamp(datetime.now(timezone.utc)).tz_localize(None)


class LiveFeed:
    """
    Polls BinanceProvider for one symbol's OHLCV on a timer aligned to
    a candle timeframe, and hands back only newly-closed candles -
    never the currently-forming one, and never the same candle twice.
    """

    def __init__(
        self,
        symbol: str,
        timeframe: str | None = None,
        candle_limit: int | None = None,
        poll_buffer_seconds: int | None = None,
        provider: BinanceProvider | None = None,
    ):

        self.symbol = symbol
        self.timeframe = timeframe or settings.timeframe
        self.candle_limit = candle_limit or settings.candle_limit

        self.poll_buffer_seconds = (
            poll_buffer_seconds
            if poll_buffer_seconds is not None
            else settings.live_poll_buffer_seconds
        )

        self.provider = provider or BinanceProvider()

        self.interval_seconds = timeframe_to_seconds(self.timeframe)

        self.last_processed_timestamp: pd.Timestamp | None = None

    def seconds_until_next_close(
        self,
        now: pd.Timestamp | None = None,
    ) -> float:

        now = now if now is not None else utc_now()

        epoch = pd.Timestamp("1970-01-01")

        elapsed_seconds = (now - epoch).total_seconds()

        seconds_since_last_close = elapsed_seconds % self.interval_seconds

        return self.interval_seconds - seconds_since_last_close

    def wait_for_next_candle(self) -> None:

        delay = (
            self.seconds_until_next_close()
            + self.poll_buffer_seconds
        )

        time.sleep(delay)

    def fetch_closed_candles(self) -> pd.DataFrame:
        """
        Fetches the latest candles and drops the last row - a REST
        poll's most recent row may still be the candle currently
        forming, not yet closed, so only rows before it are reliably
        finalized.
        """

        df = self.provider.fetch_ohlcv(
            symbol=self.symbol,
            timeframe=self.timeframe,
            limit=self.candle_limit,
        )

        return df.iloc[:-1].reset_index(drop=True)

    def select_new_rows(
        self,
        closed: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Returns the rows of `closed` strictly newer than the last
        processed timestamp, oldest first. On the very first call (no
        prior state), only the single most recent closed candle is
        "new" - everything older is historical warmup context, not
        something to act on. Logs (never silently) if more than one
        interval passed since the last poll (missed candle(s)) -
        fetch_ohlcv always returns the last candle_limit candles from
        scratch, so a missed candle self-heals on the next poll rather
        than being lost.
        """

        if self.last_processed_timestamp is None:
            return closed.iloc[-1:]

        new_rows = closed[
            closed["timestamp"] > self.last_processed_timestamp
        ]

        if len(new_rows) > 1:

            gap = len(new_rows) - 1

            logger.warning(
                f"{self.symbol}: {gap} candle(s) missed since last poll "
                f"(last processed {self.last_processed_timestamp}, "
                f"now at {new_rows['timestamp'].iloc[-1]})"
            )

        return new_rows

    def mark_processed(self, timestamp) -> None:

        self.last_processed_timestamp = timestamp
