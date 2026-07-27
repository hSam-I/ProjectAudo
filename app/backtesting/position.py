from dataclasses import dataclass
from typing import Optional

from app.core.enums import PositionSide


@dataclass
class Position:
    """
    Represents an open trading position.
    """

    symbol: str

    side: PositionSide

    quantity: float

    entry_price: float

    entry_time: str

    stop_loss: float

    take_profit: float

    risk_amount: float

    current_price: Optional[float] = None

    def update_price(
        self,
        price: float,
    ) -> None:

        self.current_price = price

    @property
    def is_long(self) -> bool:

        return self.side == PositionSide.LONG

    @property
    def is_short(self) -> bool:

        return self.side == PositionSide.SHORT