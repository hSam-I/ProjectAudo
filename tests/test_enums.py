from app.core.enums import OrderStatus
from app.core.enums import OrderType
from app.core.enums import Signal


def test_signal_enum():

    assert Signal.BUY == "BUY"
    assert Signal.SELL == "SELL"
    assert Signal.HOLD == "HOLD"


def test_order_type_enum():

    assert OrderType.MARKET == "MARKET"
    assert OrderType.LIMIT == "LIMIT"


def test_order_status_enum():

    assert OrderStatus.NEW == "NEW"
    assert OrderStatus.FILLED == "FILLED"
    assert OrderStatus.CANCELLED == "CANCELLED"
    assert OrderStatus.REJECTED == "REJECTED"