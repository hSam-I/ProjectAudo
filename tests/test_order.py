from app.execution.order import Order


def test_order_creation():

    order = Order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=0.25,
        price=65000,
        timestamp="2026-01-01",
    )

    assert order.symbol == "BTCUSDT"

    assert order.side == "BUY"

    assert order.order_type == "MARKET"

    assert order.quantity == 0.25

    assert order.price == 65000

    assert order.status == "NEW"