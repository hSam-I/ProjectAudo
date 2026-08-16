import time

import pandas as pd

from app.config.settings import settings
from app.core.time_utils import timeframe_to_seconds, utc_now
from app.data.binance_provider import BinanceProvider
from app.logging.logger import logger

# Re-exported so app.execution.live_feed stays the one stable import
# point for callers/tests that predate the move to app.core.time_utils
# (done so the network-free --live-status/web read path can use these
# without pulling in BinanceProvider's ccxt dependency).
__all__ = ["LiveFeed", "timeframe_to_seconds", "utc_now"]


class LiveFeed:
    """
    Polls BinanceProvider for one symbol's OHLCV on a timer aligned to
    a candle timeframe, and hands back only newly-closed candles -
    never the currently-forming one, and never the same candle twice.

    No unbounded in-memory buffer here to cap: fetch_closed_candles()
    re-fetches a fresh, bounded (candle_limit - 1 row) window from the
    API on every poll rather than accumulating history across calls,
    so this class's own memory footprint is already constant
    regardless of how long the process runs. The only state that does
    grow over a long run lives in Backtester.portfolio (trades/
    balance_history, one entry per trade/close) - deliberately left
    untouched here (see LiveTrader), and not a practical concern at
    any realistic paper-trading horizon.
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
