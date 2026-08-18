from dataclasses import dataclass

from app.arbitrage.funding_data_provider import FundingDataProvider
from app.arbitrage.position import ArbitragePosition
from app.broker.fee_model import FeeModel
from app.broker.slippage_model import SlippageModel
from app.logging.logger import logger


def to_perpetual_symbol(spot_symbol: str) -> str:
    """
    ccxt's unified notation for a USDT-margined Binance perpetual,
    derived from the spot symbol (e.g. "BTC/USDT" -> "BTC/USDT:USDT").
    Single source of truth so this suffix convention lives in exactly
    one place.
    """

    return f"{spot_symbol}:USDT"


class UnbalancedPositionError(Exception):
    """
    Raised when one leg of a two-leg open/close failed AND the
    automatic unwind/rollback of the already-filled leg also failed -
    the position is left with real, single-leg market exposure and
    status="UNBALANCED". Never silently swallowed - this is the exact
    operational failure mode the funding-arbitrage plan's Faz 2 exists
    to rehearse instead of assuming away.
    """


@dataclass
class LegFill:

    price: float
    quantity: float
    fee: float


class ArbitrageExecutor:
    """
    Sequential (deliberately NOT atomic) two-leg simulated fill for a
    funding-arbitrage position. "Sequential" means each leg is its own
    real-time ticker fetch + slippage + fee, one after another - the
    same failure mode a live version would have (there is no cross-
    market atomic execution), which is the whole point of this phase:
    rehearsing leg desync instead of assuming it away. See
    UnbalancedPositionError for what happens when a rollback itself
    fails.

    Opens spot-then-perp (so a perp failure unwinds an easy, unlevered
    spot position). Closes perp-then-spot (so a spot-close failure
    leaves the position naked LONG - bounded risk - rather than naked
    SHORT under leverage, which is the leg this whole strategy exists
    to protect against).
    """

    def __init__(
        self,
        data_provider: FundingDataProvider,
        spot_fee_rate: float,
        futures_fee_rate: float,
        slippage_rate: float,
    ):

        self.data_provider = data_provider

        self.spot_fee_model = FeeModel(fee_rate=spot_fee_rate)
        self.futures_fee_model = FeeModel(fee_rate=futures_fee_rate)
        self.slippage_model = SlippageModel(slippage_rate=slippage_rate)

    # --------------------------------------------------
    # OPEN
    # --------------------------------------------------

    def open_position(
        self,
        symbol: str,
        notional: float,
        leverage: int,
        maintenance_margin_rate: float,
        timestamp: str,
    ) -> ArbitragePosition:
        """
        Buys `notional` USDT worth of spot `symbol`, then opens a
        matching-quantity perpetual short. If the perp leg fails, the
        spot leg is automatically sold back (unwound) rather than left
        as an accidental naked long; the ORIGINAL perp-leg exception is
        then re-raised so the caller knows the open attempt produced no
        position. If the unwind itself also fails, raises
        UnbalancedPositionError instead - real single-leg exposure that
        needs manual attention, never silently retried.
        """

        spot_fill = self._fill_spot_leg_buy(symbol, notional)

        try:

            perp_fill = self._fill_perp_leg_open_short(
                symbol, spot_fill.quantity,
            )

        except Exception as perp_error:

            logger.error(
                f"{symbol}: perp leg failed while opening "
                f"({perp_error}) - unwinding spot leg"
            )

            try:

                unwind_fill = self._fill_spot_leg_sell(
                    symbol, spot_fill.quantity,
                )

            except Exception as unwind_error:

                raise UnbalancedPositionError(
                    f"{symbol}: perp leg failed to open ({perp_error}) "
                    f"AND the spot-leg unwind also failed "
                    f"({unwind_error}) - position left one-legged "
                    "(naked spot long), manual intervention required"
                ) from unwind_error

            logger.warning(
                f"{symbol}: spot leg unwound successfully after perp "
                f"leg failure (unwind fee={unwind_fill.fee:.4f}) - "
                "no position was opened"
            )

            raise

        margin = (
            perp_fill.price
            * perp_fill.quantity
            / leverage
        )

        return ArbitragePosition(
            symbol=symbol,
            leverage=leverage,
            maintenance_margin_rate=maintenance_margin_rate,
            entry_time=timestamp,
            spot_entry_price=spot_fill.price,
            spot_qty=spot_fill.quantity,
            perp_entry_price=perp_fill.price,
            perp_qty=perp_fill.quantity,
            margin=margin,
            status="OPEN",
        )

    # --------------------------------------------------
    # CLOSE
    # --------------------------------------------------

    def close_position(
        self,
        position: ArbitragePosition,
        timestamp: str,
    ) -> ArbitragePosition:
        """
        Closes the perp leg first, then the spot leg. If the perp leg
        fails, nothing has been touched yet - the position is left
        untouched (still "OPEN") and the exception propagates directly,
        safe to retry. If the spot leg fails AFTER the perp leg already
        closed, the position is marked "UNBALANCED" (naked spot long,
        the hedge is gone) and UnbalancedPositionError is raised -
        real exposure that needs manual attention.
        """

        perp_fill = self._fill_perp_leg_close_short(
            position.symbol, position.perp_qty,
        )

        try:

            spot_fill = self._fill_spot_leg_sell(
                position.symbol, position.spot_qty,
            )

        except Exception as spot_error:

            position.status = "UNBALANCED"

            logger.error(
                f"{position.symbol}: perp leg closed but the spot leg "
                f"failed to close ({spot_error}) - position is now "
                "naked LONG on spot, marked UNBALANCED"
            )

            raise UnbalancedPositionError(
                f"{position.symbol}: perp leg closed but spot leg "
                f"failed to close ({spot_error}) - position left "
                "one-legged (naked spot long), manual intervention "
                "required"
            ) from spot_error

        position.status = "CLOSED"
        position.exit_time = timestamp
        position.exit_spot_price = spot_fill.price
        position.exit_perp_price = perp_fill.price

        return position

    # --------------------------------------------------
    # LEG FILLS
    # --------------------------------------------------

    def _fill_spot_leg_buy(self, symbol: str, notional: float) -> LegFill:

        market_price = self.data_provider.spot.fetch_ticker(symbol)

        execution_price = self.slippage_model.buy_price(market_price)

        quantity = notional / execution_price

        fee = self.spot_fee_model.calculate(execution_price, quantity)

        return LegFill(price=execution_price, quantity=quantity, fee=fee)

    def _fill_spot_leg_sell(self, symbol: str, quantity: float) -> LegFill:

        market_price = self.data_provider.spot.fetch_ticker(symbol)

        execution_price = self.slippage_model.sell_price(market_price)

        fee = self.spot_fee_model.calculate(execution_price, quantity)

        return LegFill(price=execution_price, quantity=quantity, fee=fee)

    def _fill_perp_leg_open_short(
        self, symbol: str, quantity: float,
    ) -> LegFill:
        """Opening a short = selling the perpetual contract."""

        perp_symbol = to_perpetual_symbol(symbol)

        market_price = self.data_provider.fetch_perp_ticker(perp_symbol)

        execution_price = self.slippage_model.sell_price(market_price)

        fee = self.futures_fee_model.calculate(execution_price, quantity)

        return LegFill(price=execution_price, quantity=quantity, fee=fee)

    def _fill_perp_leg_close_short(
        self, symbol: str, quantity: float,
    ) -> LegFill:
        """Closing a short = buying the perpetual contract back."""

        perp_symbol = to_perpetual_symbol(symbol)

        market_price = self.data_provider.fetch_perp_ticker(perp_symbol)

        execution_price = self.slippage_model.buy_price(market_price)

        fee = self.futures_fee_model.calculate(execution_price, quantity)

        return LegFill(price=execution_price, quantity=quantity, fee=fee)
