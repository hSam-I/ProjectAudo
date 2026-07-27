from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.core.enums import OrderSide
from app.reporting.expectancy import Expectancy


def test_expectancy():

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
    t1.profit = 200

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

    expectancy = Expectancy.calculate(portfolio)

    assert expectancy == 50.0