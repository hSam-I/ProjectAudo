from app.backtesting.backtester import Backtester
from app.config.settings import settings
from app.decision.decision_engine import DecisionEngine
from app.execution.live_feed import LiveFeed
from app.execution.live_state_store import LiveStateStore
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

    def run_forever(self) -> None:

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

            self.feed.wait_for_next_candle()

            self.poll_once()

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

    def _paper_trade_step(self, enriched, row) -> None:

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
