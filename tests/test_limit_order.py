from app.execution.order import Order


def test_limit_order():

    order = Order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=1,
        price=64000,
        timestamp="2026-01-01",
    )

    assert order.is_limit()

    assert not order.is_market()