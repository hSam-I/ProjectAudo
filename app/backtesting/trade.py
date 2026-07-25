from dataclasses import dataclass


@dataclass
class Trade:
    symbol: str

    side: str

    entry_price: float

    exit_price: float

    quantity: float

    profit: float

    entry_time: str

    exit_time: str