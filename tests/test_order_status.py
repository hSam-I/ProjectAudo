from app.execution.order import Order


def test_order_status():

    order = Order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=1,
        price=65000,
        timestamp="2026-01-01",
    )

    assert order.status == "NEW"

    assert order.can_fill(65100)

    order.fill(
        price=65010,
        timestamp="2026-01-01 10:00",
    )

    assert order.status == "FILLED"

    assert order.filled_price == 65010

    order.cancel()

    assert order.status == "CANCELLED"