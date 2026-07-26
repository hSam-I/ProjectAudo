from app.execution.order import Order
from app.execution.order_book import OrderBook


def test_pending_orders():

    book = OrderBook()

    order1 = Order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=1,
        price=64000,
        timestamp="2026-01-01",
    )

    order2 = Order(
        symbol="ETHUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=1,
        price=3000,
        timestamp="2026-01-01",
    )

    book.add(order1)

    book.add(order2)

    order2.fill(
        price=3000,
        timestamp="2026-01-01",
    )

    pending = book.pending()

    assert len(pending) == 1

    assert pending[0].symbol == "BTCUSDT"