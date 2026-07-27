from dataclasses import dataclass
from typing import Optional

from app.core.enums import OrderStatus
from app.core.enums import OrderType


@dataclass
class Order:
    """
    Represents an order sent to a broker.
    """

    symbol: str

    side: str

    order_type: OrderType

    quantity: float

    price: float

    timestamp: str

    status: OrderStatus = OrderStatus.NEW

    order_id: Optional[int] = None

    filled_price: Optional[float] = None

    filled_time: Optional[str] = None

    def is_market(self):

        return self.order_type == OrderType.MARKET

    def is_limit(self):

        return self.order_type == OrderType.LIMIT

    def can_fill(self, market_price: float):

        if self.is_market():
            return True

        if self.side == "BUY":
            return market_price <= self.price

        return market_price >= self.price

    def fill(
        self,
        price: float,
        timestamp: str,
    ):

        self.filled_price = price

        self.filled_time = timestamp

        self.status = OrderStatus.FILLED

    def cancel(self):

        self.status = OrderStatus.CANCELLED

    def reject(self):

        self.status = OrderStatus.REJECTED