import time

import pandas as pd

from app.arbitrage.arbitrage_state_store import (
    ArbitrageStateCorruptError,
    ArbitrageStateStore,
)
from app.arbitrage.arbitrage_status_store import ArbitrageStatusStore
from app.arbitrage.execution import (
    ArbitrageExecutor,
    UnbalancedPositionError,
    to_perpetual_symbol,
)
from app.arbitrage.funding_data_provider import FundingDataProvider
from app.arbitrage.position import (
    apply_funding_payment,
    compute_deployable_notional,
    compute_margin_ratio,
    consecutive_negative_funding_streak,
    is_liquidation_warning,
)
from app.config.settings import settings
from app.core.time_utils import utc_now
from app.logging.logger import logger

FUNDING_INTERVAL_SECONDS = 8 * 60 * 60

# Comfortably above the funding-arbitrage measurement's observed
# spot/perp basis (BTC/ETH, 2019-2026: std ~0.07-0.08%, 99th
# percentile ~0.2%, excluding perp-market-launch-day outliers) -
# refuses to open into a clearly abnormal market. A sanity guard, not
# a tunable risk parameter, so it isn't a settings field.
MAX_SANE_BASIS_PCT = 0.005


class FundingArbitrageTrader:
    """
    Polls funding settlements for one symbol and, if
    settings.enable_funding_arbitrage is True, opens (once conditions
    are sane) and then holds a delta-neutral spot-long + perp-short
    position collecting funding - see the funding-arbitrage plan
    (CLAUDE.md). With enable_funding_arbitrage=False, stays observe-
    only forever (mirrors LiveTrader's enable_live_paper_trading gate).

    Every poll is wrapped by run_forever() the same way LiveTrader
    wraps poll_once(): a transient error is logged, counted, and
    retried after a pause - EXCEPT UnbalancedPositionError, which is
    never treated as transient (see UnbalancedPositionError's
    docstring) and stops the loop instead, and
    ArbitrageStateCorruptError from a corrupt arbitrage_state.json,
    which is the same kind of "real trading history, never silently
    reset" failure LiveStateCorruptError represents for the other
    live-trading system.
    """

    def __init__(
        self,
        symbol: str | None = None,
        data_provider: FundingDataProvider | None = None,
        executor: ArbitrageExecutor | None = None,
    ):

        self.symbol = symbol or settings.funding_arb_symbol
        self.perp_symbol = to_perpetual_symbol(self.symbol)

        self.data_provider = data_provider or FundingDataProvider()

        self.executor = executor or ArbitrageExecutor(
            data_provider=self.data_provider,
            spot_fee_rate=settings.commission,
            futures_fee_rate=settings.funding_arb_futures_fee,
            slippage_rate=settings.slippage,
        )

        self._started_at = utc_now()
        self._poll_count = 0
        self._error_count = 0
        self._last_error: str | None = None
        self._last_poll_at = None

        try:
            previous_status = ArbitrageStatusStore.load()
        except ArbitrageStateCorruptError as e:
            # Pure heartbeat, no trading history worth protecting -
            # same reasoning as LiveTrader's handling of a corrupt
            # live_status.json.
            logger.warning(
                f"{self.symbol}: previous arbitrage_status.json is "
                f"corrupt, restart_count will reset to 0: {e}"
            )
            previous_status = None

        self._restart_count = (
            previous_status["restart_count"] + 1
            if previous_status is not None
            else 0
        )

        # Unlike ArbitrageStatusStore above, a corrupt
        # arbitrage_state.json is NOT caught here - it carries real
        # funding-collection history, so this deliberately propagates
        # and prevents the trader from ever starting rather than
        # silently discarding months of history.
        self.position, self.closed_positions = ArbitrageStateStore.restore()

        if self.position is not None:

            logger.info(
                f"{self.symbol}: restored an open funding-arbitrage "
                f"position (status={self.position.status}, "
                f"cumulative_funding={self.position.cumulative_funding:+.4f})"
            )

    # --------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------

    def run_forever(self) -> None:

        logger.info(
            f"{self.symbol}: starting funding-arbitrage paper trading "
            "loop (no real orders will ever be sent)"
        )

        while True:

            self._save_status_heartbeat()

            self._wait_for_next_funding()

            try:

                self.poll_once()

                self._poll_count += 1
                self._last_poll_at = utc_now()

            except UnbalancedPositionError as e:

                logger.error(
                    f"{self.symbol}: position left UNBALANCED, "
                    f"stopping (manual intervention required): {e}"
                )

                raise

            except ArbitrageStateCorruptError as e:

                logger.error(
                    f"{self.symbol}: arbitrage state is corrupt, "
                    f"stopping (see error above): {e}"
                )

                raise

            except Exception as e:

                self._error_count += 1
                self._last_error = str(e)

                logger.error(
                    f"{self.symbol}: error during funding-arbitrage "
                    f"poll, retrying in "
                    f"{settings.live_error_retry_seconds}s: {e}"
                )

                time.sleep(settings.live_error_retry_seconds)

    def seconds_until_next_funding(
        self,
        now: pd.Timestamp | None = None,
    ) -> float:

        now = now if now is not None else utc_now()

        epoch = pd.Timestamp("1970-01-01")

        elapsed_seconds = (now - epoch).total_seconds()

        seconds_since_last_funding = (
            elapsed_seconds % FUNDING_INTERVAL_SECONDS
        )

        return FUNDING_INTERVAL_SECONDS - seconds_since_last_funding

    def _wait_for_next_funding(self) -> None:

        delay = (
            self.seconds_until_next_funding()
            + settings.funding_arb_poll_buffer_seconds
        )

        time.sleep(delay)

    # --------------------------------------------------
    # ONE POLL
    # --------------------------------------------------

    def poll_once(self) -> None:

        timestamp = str(utc_now())

        funding_rate = self.data_provider.fetch_funding_rate(
            self.perp_symbol
        )

        if self.position is None:
            self._maybe_open(funding_rate, timestamp)
        else:
            self._manage_open_position(funding_rate, timestamp)

        # Deliberately NOT failure-isolated (unlike
        # _save_status_heartbeat below) - this carries real trading
        # state, so a write failure here is a genuine poll error that
        # should be logged/retried by run_forever's generic handler,
        # not silently swallowed. Mirrors LiveStateStore.save() being
        # called unwrapped in LiveTrader._paper_trade_step.
        ArbitrageStateStore.save(self.position, self.closed_positions)

    def _maybe_open(self, funding_rate: float, timestamp: str) -> None:

        if not settings.enable_funding_arbitrage:

            logger.info(
                f"{self.symbol}: observe only "
                "(enable_funding_arbitrage=False), "
                f"current funding_rate={funding_rate:.6f}"
            )

            return

        spot_price = self.data_provider.spot.fetch_ticker(self.symbol)
        perp_price = self.data_provider.fetch_perp_ticker(self.perp_symbol)

        can_open, reason = self._sanity_check(
            funding_rate, spot_price, perp_price,
        )

        if not can_open:

            logger.info(
                f"{self.symbol}: not opening this poll ({reason})"
            )

            return

        notional = compute_deployable_notional(
            settings.starting_balance,
            settings.funding_arb_leverage,
        )

        self.position = self.executor.open_position(
            self.symbol,
            notional=notional,
            leverage=settings.funding_arb_leverage,
            maintenance_margin_rate=(
                settings.funding_arb_maintenance_margin_rate
            ),
            timestamp=timestamp,
        )

        logger.info(
            f"{self.symbol}: funding-arbitrage position opened "
            f"(notional={notional:.2f}, leverage="
            f"{settings.funding_arb_leverage}x)"
        )

    @staticmethod
    def _sanity_check(
        funding_rate: float,
        spot_price: float,
        perp_price: float,
    ) -> tuple:

        if funding_rate < 0:

            return (
                False,
                f"current funding rate is negative ({funding_rate:.6f})",
            )

        basis_pct = abs(perp_price - spot_price) / spot_price

        if basis_pct > MAX_SANE_BASIS_PCT:

            return (
                False,
                f"basis {basis_pct:.4%} exceeds sanity threshold "
                f"({MAX_SANE_BASIS_PCT:.2%})",
            )

        return True, None

    def _manage_open_position(
        self, funding_rate: float, timestamp: str,
    ) -> None:

        mark_price = self.data_provider.fetch_perp_ticker(self.perp_symbol)

        payment = apply_funding_payment(
            self.position, funding_rate, mark_price, timestamp,
        )

        logger.info(
            f"{self.symbol}: funding settled, rate={funding_rate:.6f} "
            f"payment={payment:+.4f} "
            f"cumulative={self.position.cumulative_funding:+.4f}"
        )

        margin_ratio = compute_margin_ratio(self.position, mark_price)

        if is_liquidation_warning(
            self.position,
            mark_price,
            settings.funding_arb_liquidation_warning_pct,
        ):

            logger.error(
                f"{self.symbol}: margin ratio {margin_ratio:.4f} "
                "reached the liquidation warning threshold "
                f"({settings.funding_arb_liquidation_warning_pct}) - "
                "force-closing position"
            )

            self._close(timestamp, reason="liquidation_warning")

            return

        streak = consecutive_negative_funding_streak(
            self.position.funding_events
        )

        if streak >= settings.funding_arb_max_negative_streak:

            logger.error(
                f"{self.symbol}: {streak} consecutive negative "
                "funding periods (circuit breaker at "
                f"{settings.funding_arb_max_negative_streak}) - "
                "force-closing position"
            )

            self._close(timestamp, reason="negative_funding_streak")

    def _close(self, timestamp: str, reason: str) -> None:
        """
        Routed through ArbitrageExecutor.close_position() specifically
        so Faz 2's sequential-fill/UNBALANCED-detection/unwind
        guarantees stay in effect for every automatic close, not just
        operator-triggered ones - see the funding-arbitrage plan.
        """

        closed = self.executor.close_position(self.position, timestamp)

        logger.info(
            f"{self.symbol}: position closed ({reason}), "
            f"cumulative_funding={closed.cumulative_funding:+.4f}"
        )

        self.closed_positions.append(closed)

        self.position = None

    # --------------------------------------------------
    # TELEMETRY
    # --------------------------------------------------

    def _save_status_heartbeat(self) -> None:
        """
        Failure-isolated on purpose, same reasoning as LiveTrader's
        _save_status_heartbeat: pure telemetry must never break the
        trading loop. Even the margin_ratio price fetch inside it is
        separately guarded, so a failed price lookup degrades the
        heartbeat (margin_ratio=None) instead of skipping the write
        entirely.
        """

        try:

            margin_ratio = None

            if self.position is not None:

                try:

                    mark_price = self.data_provider.fetch_perp_ticker(
                        self.perp_symbol
                    )

                    margin_ratio = compute_margin_ratio(
                        self.position, mark_price,
                    )

                except Exception:
                    pass

            ArbitrageStatusStore.save(
                symbol=self.symbol,
                started_at=self._started_at,
                restart_count=self._restart_count,
                last_poll_at=self._last_poll_at,
                next_poll_due_at=(
                    utc_now()
                    + pd.Timedelta(
                        seconds=self.seconds_until_next_funding()
                    )
                ),
                poll_count=self._poll_count,
                error_count=self._error_count,
                last_error=self._last_error,
                position_status=(
                    self.position.status
                    if self.position is not None
                    else None
                ),
                margin_ratio=margin_ratio,
                cumulative_funding=(
                    self.position.cumulative_funding
                    if self.position is not None
                    else None
                ),
            )

        except Exception as e:

            logger.warning(
                f"{self.symbol}: failed to write funding-arbitrage "
                f"status heartbeat: {e}"
            )
