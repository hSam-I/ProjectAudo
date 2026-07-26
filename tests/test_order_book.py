from app.execution.order import Order
from app.execution.order_book import OrderBook


def test_order_book():

    book = OrderBook()

    order = Order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=1,
        price=65000,
        timestamp="2026-01-01",
    )

    book.add(order)

    assert book.count() == 1

    assert order.order_id == 1

    assert book.get(1) == order

    pending = book.pending()

    assert len(pending) == 1

    order.fill(
        price=65000,
        timestamp="2026-01-01",
    )

    assert len(book.pending()) == 0