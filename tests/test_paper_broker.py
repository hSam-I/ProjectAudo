from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.broker.paper_broker import PaperBroker


def test_paper_broker():

    portfolio = Portfolio(10000)

    broker = PaperBroker(portfolio)

    trade = Trade(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=100,
        quantity=1,
        entry_time="2026-01-01",
        stop_loss=95,
        take_profit=110,
        risk_amount=100,
    )

    broker.buy(trade)

    assert portfolio.total_trades == 1

    assert broker.order_book.count() == 1

    order = broker.order_book.get(1)

    assert order.status == "FILLED"

    trade.close(
        exit_price=110,
        exit_time="2026-01-02",
        reason="TAKE_PROFIT",
    )

    broker.close(trade)

    assert portfolio.closed_trades_count == 1