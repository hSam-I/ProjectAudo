from dataclasses import dataclass
from typing import Optional


@dataclass
class Order:
    """
    Represents an order sent to a broker.
    """

    symbol: str

    side: str

    order_type: str

    quantity: float

    price: float

    timestamp: str

    status: str = "NEW"

    order_id: Optional[int] = None

    filled_price: Optional[float] = None

    filled_time: Optional[str] = None

    def is_market(self):

        return self.order_type == "MARKET"

    def is_limit(self):

        return self.order_type == "LIMIT"

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

        self.status = "FILLED"

    def cancel(self):

        self.status = "CANCELLED"

    def reject(self):

        self.status = "REJECTED"