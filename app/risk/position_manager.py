from app.backtesting.trade import Trade
from app.risk.break_even import BreakEven
from app.risk.trailing_stop import TrailingStop


class PositionManager:
    """
    Central position management.

    Responsible for:

    - Break-even Stop
    - Trailing Stop
    - Partial Take Profit (future)
    """

    @staticmethod
    def update(
        trade: Trade,
        current_price: float,
        atr: float,
    ) -> None:

        PositionManager._update_break_even(
            trade,
            current_price,
            atr,
        )

        PositionManager._update_trailing_stop(
            trade,
            current_price,
            atr,
        )

    @staticmethod
    def _update_break_even(
        trade: Trade,
        current_price: float,
        atr: float,
    ) -> None:

        trade.stop_loss = BreakEven.update(
            entry_price=trade.entry_price,
            current_price=current_price,
            current_stop=trade.stop_loss,
            atr=atr,
        )

    @staticmethod
    def _update_trailing_stop(
        trade: Trade,
        current_price: float,
        atr: float,
    ) -> None:

        trade.stop_loss = TrailingStop.update(
            current_stop=trade.stop_loss,
            current_price=current_price,
            atr=atr,
        )