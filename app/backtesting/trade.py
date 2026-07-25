from dataclasses import dataclass


@dataclass
class Trade:

    symbol: str

    side: str

    entry_price: float

    quantity: float

    entry_time: str

    exit_price: float | None = None

    exit_time: str | None = None

    profit: float = 0.0

    is_open: bool = True

    def close(self, exit_price: float, exit_time: str):

        self.exit_price = exit_price

        self.exit_time = exit_time

        self.profit = (
            exit_price - self.entry_price
        ) * self.quantity

        self.is_open = False