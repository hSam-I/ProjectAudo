from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.core.enums import OrderSide
from app.reporting.performance import Performance


def test_win_rate():

    portfolio = Portfolio(10000)

    t1 = Trade(
        symbol="BTC",
        side=OrderSide.BUY,
        entry_price=100,
        quantity=1,
        entry_time="1",
        stop_loss=90,
        take_profit=120,
        risk_amount=100,
    )

    t1.profit = 100

    t2 = Trade(
        symbol="BTC",
        side=OrderSide.BUY,
        entry_price=100,
        quantity=1,
        entry_time="2",
        stop_loss=90,
        take_profit=120,
        risk_amount=100,
    )

    t2.profit = -50

    portfolio.closed_trades.append(t1)
    portfolio.closed_trades.append(t2)

    assert Performance.total_trades(portfolio) == 2

    assert Performance.winning_trades(portfolio) == 1

    assert Performance.losing_trades(portfolio) == 1

    assert Performance.win_rate(portfolio) == 0.5