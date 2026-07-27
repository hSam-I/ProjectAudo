from enum import StrEnum


class Signal(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(StrEnum):
    NEW = "NEW"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"