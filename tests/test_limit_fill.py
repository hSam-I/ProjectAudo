from app.execution.order import Order


def test_limit_fill():

    order = Order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=1,
        price=64000,
        timestamp="2026-01-01",
    )

    assert not order.can_fill(64500)

    assert not order.can_fill(64100)

    assert order.can_fill(64000)

    assert order.can_fill(63900)