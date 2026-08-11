from dataclasses import dataclass, field
from typing import Optional

from app.core.enums import OrderSide


@dataclass
class Trade:
    """
    Represents a single trade.
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

    # NEW
    partial_tp_taken: bool = False
    remaining_quantity: float = 0.0

    contributing_strategies: list[str] = field(default_factory=list)

    def __post_init__(self):

        self.remaining_quantity = self.quantity

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

        self.recalculate_profit()

    def recalculate_profit(self) -> None:
        """
        Recomputes profit from the current entry/exit price.

        Needed because exit_price can change after close() (e.g.
        execution slippage), and profit must stay consistent with it.
        """

        if self.side == OrderSide.BUY:

            self.profit = (
                self.exit_price - self.entry_price
            ) * self.remaining_quantity

        else:

            self.profit = (
                self.entry_price - self.exit_price
            ) * self.remaining_quantity