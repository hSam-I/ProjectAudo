from app.backtesting.portfolio import Portfolio
from app.broker.paper_broker import PaperBroker
from app.execution.order import Order


def test_market_processing():

    broker = PaperBroker(
        Portfolio(10000)
    )

    order = Order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=1,
        price=64000,
        timestamp="2026-01-01",
    )

    broker.order_book.add(order)

    broker.process_market_price(
        market_price=64500,
        timestamp="2026-01-01",
    )

    assert order.status == "NEW"

    broker.process_market_price(
        market_price=64000,
        timestamp="2026-01-01",
    )

    assert order.status == "FILLED"