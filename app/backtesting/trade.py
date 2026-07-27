from dataclasses import dataclass
from typing import Optional

from app.core.enums import OrderSide


@dataclass
class Trade:
    """
    Represents a single trade.

    The same model is intended to be used by both
    the Backtester and the future Live Execution Engine.
    """

    symbol: str

    side: OrderSide

    entry_price: float
    quantity: float
    entry_time: str

    stop_loss: float
    take_profit: float
    risk_amount: float

    exit_price: Optional[float] = None
    exit_time: Optional[str] = None

    status: str = "OPEN"

    profit: float = 0.0

    exit_reason: Optional[str] = None

    def close(
        self,
        exit_price: float,
        exit_time: str,
        reason: str = "SIGNAL",
    ) -> None:

        self.exit_price = exit_price
        self.exit_time = exit_time

        self.status = "CLOSED"

        self.exit_reason = reason

        if self.side == OrderSide.BUY:

            self.profit = (
                exit_price - self.entry_price
            ) * self.quantity

        else:

            self.profit = (
                self.entry_price - exit_price
            ) * self.quantity