from app.backtesting.trade import Trade
from app.risk.trailing_stop import TrailingStop


class PositionManager:
    """
    Central position management.

    Responsible for:

    - Trailing Stop
    - Break-even Stop (future)
    - Partial Take Profit (future)
    """

    @staticmethod
    def update(
        trade: Trade,
        current_price: float,
        atr: float,
    ) -> None:

        PositionManager._update_trailing_stop(
            trade,
            current_price,
            atr,
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