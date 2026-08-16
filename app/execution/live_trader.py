import time

import pandas as pd

from app.backtesting.backtester import Backtester
from app.config.settings import settings
from app.core.time_utils import utc_now
from app.decision.decision_engine import DecisionEngine
from app.execution.live_decision_log import LiveDecisionLog
from app.execution.live_feed import LiveFeed
from app.execution.live_state_store import LiveStateCorruptError, LiveStateStore
from app.execution.live_status_store import LiveStatusStore
from app.indicators.indicator_engine import IndicatorEngine
from app.logging.logger import logger


class LiveTrader:
    """
    Polls a LiveFeed on every closed candle and runs the same
    indicator + DecisionEngine pipeline the backtester uses.

    - settings.enable_live_paper_trading=False (default): OBSERVE ONLY
      - just logs what would have been decided. No Backtester/
      PaperBroker/Portfolio is ever touched in this mode.
    - settings.enable_live_paper_trading=True: PAPER TRADING - reuses
      Backtester._step() UNCHANGED (same signature, same internal
      logic as backtesting/multi-position) to actually open/manage/
      close trades through PaperBroker, filled at a real-time price
      (BinanceProvider.fetch_ticker) rather than a candle's close.
      Still never sends a real order - see PaperBroker/ExecutionEngine,
      which only ever mutate an in-memory Portfolio.
    """

    def __init__(
        self,
        symbol: str,
        feed: LiveFeed | None = None,
        decision_engine: DecisionEngine | None = None,
    ):

        self.symbol = symbol
        self.feed = feed or LiveFeed(symbol)
        self.decision_engine = decision_engine or DecisionEngine()

        self.backtester: Backtester | None = None

        # Deliberately not named broker/portfolio/portfolio_manager -
        # test_live_trader_never_constructs_a_broker_or_portfolio()
        # asserts those three attribute names are absent whenever no
        # trade could have been opened.
        self._started_at = utc_now()
        self._poll_count = 0
        self._error_count = 0
        self._last_error: str | None = None
        self._last_poll_at = None

        try:
            previous_status = LiveStatusStore.load()
        except LiveStateCorruptError as e:
            # Unlike live_state.json (the actual paper-trading
            # portfolio), a corrupt heartbeat file carries no trading
            # history worth protecting - starting fresh (restart_count
            # resets to 0) is safe and lets the loop come up instead of
            # refusing to start over a stale telemetry file.
            logger.warning(
                f"{symbol}: previous live_status.json is corrupt, "
                f"restart_count will reset to 0: {e}"
            )
            previous_status = None

        self._restart_count = (
            previous_status["restart_count"] + 1
            if previous_status is not None
            else 0
        )

    def run_forever(self) -> None:
        """
        Runs indefinitely. Each poll is wrapped so a transient failure
        (network hiccup, exchange rate limit, ...) logs and retries
        after a short pause instead of crashing a process meant to run
        for weeks - except LiveStateCorruptError, which is NEVER
        treated as transient (retrying can't fix a corrupt file, and
        silently continuing on unreadable state could mean quietly
        losing the paper-trading history), so it's left to propagate
        and stop the loop with a clear error.
        """

        if settings.enable_live_paper_trading:

            logger.info(
                f"{self.symbol}: starting live PAPER TRADING "
                "(no real orders will ever be sent)"
            )

        else:

            logger.info(
                f"{self.symbol}: starting live observation "
                "(OBSERVE ONLY - no trades will be opened)"
            )

        while True:

            self._save_status_heartbeat()

            self.feed.wait_for_next_candle()

            try:

                self.poll_once()

                self._poll_count += 1
                self._last_poll_at = utc_now()

            except LiveStateCorruptError:

                logger.error(
                    f"{self.symbol}: live state is corrupt, stopping "
                    "(see error above) - fix or remove the state file "
                    "and restart"
                )

                raise

            except Exception as e:

                self._error_count += 1
                self._last_error = str(e)

                logger.error(
                    f"{self.symbol}: error during live poll, retrying "
                    f"in {settings.live_error_retry_seconds}s: {e}"
                )

                time.sleep(settings.live_error_retry_seconds)

    def _save_status_heartbeat(self) -> None:
        """
        Failure-isolated on purpose: a heartbeat write is pure
        telemetry, so a transient error here (e.g. a Windows reader
        holding the file open across an os.replace()) must never break
        the trading loop the way a real poll error would.
        """

        try:

            next_poll_due_at = utc_now() + pd.Timedelta(
                seconds=self.feed.seconds_until_next_close()
            )

            LiveStatusStore.save(
                symbol=self.symbol,
                mode=(
                    "paper"
                    if settings.enable_live_paper_trading
                    else "observe"
                ),
                started_at=self._started_at,
                restart_count=self._restart_count,
                last_poll_at=self._last_poll_at,
                next_poll_due_at=next_poll_due_at,
                poll_count=self._poll_count,
                error_count=self._error_count,
                last_error=self._last_error,
            )

        except Exception as e:

            logger.warning(
                f"{self.symbol}: failed to write live status heartbeat: {e}"
            )

    def poll_once(self) -> None:

        closed = self.feed.fetch_closed_candles()

        new_rows = self.feed.select_new_rows(closed)

        for _, row in new_rows.iterrows():

            history = closed[
                closed["timestamp"] <= row["timestamp"]
            ]

            if len(history) < settings.warmup_candles:

                logger.info(
                    f"{self.symbol} | {row['timestamp']} | "
                    f"warming up ({len(history)}/{settings.warmup_candles} candles)"
                )

                self.feed.mark_processed(row["timestamp"])

                continue

            enriched = IndicatorEngine.calculate_all(history)

            if settings.enable_live_paper_trading:
                self._paper_trade_step(enriched, row)
            else:
                self._observe_step(enriched, row)

            self.feed.mark_processed(row["timestamp"])

    def _observe_step(self, enriched, row) -> None:

        decision = self.decision_engine.evaluate(enriched)

        logger.info(
            f"{self.symbol} | {row['timestamp']} | OBSERVE ONLY | "
            f"raw={decision.raw_signal} | final={decision.signal} | "
            f"score={decision.score} | regime={decision.regime}"
        )

        self._log_decision(row["timestamp"], decision)

    def _paper_trade_step(self, enriched, row) -> None:

        # Evaluated separately from Backtester._step()'s own internal
        # evaluate() call (same DecisionEngine instance, same enriched
        # df, so identical result) rather than having _step() return
        # its Decision - keeps _step()'s signature/contract, and every
        # test pinned to it, completely untouched. main.py already
        # does this same redundant-evaluate today (see CLAUDE.md).
        decision = self.decision_engine.evaluate(enriched)

        self._log_decision(row["timestamp"], decision)

        backtester = self._ensure_backtester()

        price = self.feed.provider.fetch_ticker(self.symbol)

        execution = {
            "open": price,
            "high": price,
            "low": price,
            "close": price,
            "timestamp": row["timestamp"],
        }

        backtester._step(self.symbol, enriched, execution)

        LiveStateStore.save(
            backtester.portfolio,
            row["timestamp"],
        )

    def _log_decision(self, timestamp, decision) -> None:
        """
        Failure-isolated for the same reason as _save_status_heartbeat():
        this is pure telemetry, so a write error here (disk full, a
        concurrent reader on Windows, ...) must never interrupt trading.
        """

        try:

            LiveDecisionLog.append(
                timestamp=timestamp,
                symbol=self.symbol,
                raw_signal=decision.raw_signal,
                signal=decision.signal,
                score=decision.score,
                regime=decision.regime,
            )

        except Exception as e:

            logger.warning(
                f"{self.symbol}: failed to append live decision log entry: {e}"
            )

    def _ensure_backtester(self) -> Backtester:
        """
        Lazily creates (and caches) the Backtester used for paper
        trading, restoring prior state on first use if any exists.
        Lazy on purpose: nothing capable of opening a trade exists at
        all until paper trading has actually been engaged at least
        once, and the SAME instance must persist across polls so its
        Portfolio balance accumulates correctly.
        """

        if self.backtester is None:

            self.backtester = Backtester()

            # Share this LiveTrader's own DecisionEngine (rather than
            # the fresh one Backtester() built for itself) so observe
            # and paper-trading modes are driven by the same instance.
            self.backtester.decision_engine = self.decision_engine

            restored_timestamp = LiveStateStore.restore_into(
                self.backtester.portfolio,
                self.backtester.portfolio_manager,
            )

            if restored_timestamp is not None:

                self.feed.mark_processed(restored_timestamp)

                logger.info(
                    f"{self.symbol}: restored live paper-trading state, "
                    f"resuming after {restored_timestamp}"
                )

        return self.backtester
