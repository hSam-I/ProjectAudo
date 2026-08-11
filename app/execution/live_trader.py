from app.config.settings import settings
from app.decision.decision_engine import DecisionEngine
from app.execution.live_feed import LiveFeed
from app.indicators.indicator_engine import IndicatorEngine
from app.logging.logger import logger


class LiveTrader:
    """
    Phase 1: OBSERVE ONLY - never opens, manages, or closes a trade.

    Polls a LiveFeed on every closed candle, runs the same
    indicator + DecisionEngine pipeline the backtester uses, and logs
    what would have been decided. Deliberately constructs no
    Backtester/PaperBroker/Portfolio - there is nothing to persist
    because nothing is ever opened.
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

    def run_forever(self) -> None:

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

            decision = self.decision_engine.evaluate(enriched)

            logger.info(
                f"{self.symbol} | {row['timestamp']} | OBSERVE ONLY | "
                f"raw={decision.raw_signal} | final={decision.signal} | "
                f"score={decision.score} | regime={decision.regime}"
            )

            self.feed.mark_processed(row["timestamp"])
