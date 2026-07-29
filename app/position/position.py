from dataclasses import dataclass


@dataclass
class Position:
    """
    Represents an open trading position.
    """

    symbol: str
    side: str
    entry_price: float
    quantity: float