from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.core.enums import OrderSide
from app.reporting.profit_factor import ProfitFactor


def test_profit_factor():

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
    t1.profit = 300

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
    t2.profit = -100

    portfolio.closed_trades.append(t1)
    portfolio.closed_trades.append(t2)

    assert ProfitFactor.calculate(portfolio) == 3.0