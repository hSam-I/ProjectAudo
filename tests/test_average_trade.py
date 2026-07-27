from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.core.enums import OrderSide
from app.reporting.average_trade import AverageTrade


def test_average_trade():

    portfolio = Portfolio(10000)

    profits = [200, -100, 300]

    for i, profit in enumerate(profits):

        trade = Trade(
            symbol="BTC",
            side=OrderSide.BUY,
            entry_price=100,
            quantity=1,
            entry_time=str(i),
            stop_loss=90,
            take_profit=120,
            risk_amount=100,
        )

        trade.profit = profit

        portfolio.closed_trades.append(trade)

    assert AverageTrade.average_win(portfolio) == 250

    assert AverageTrade.average_loss(portfolio) == 100

    assert AverageTrade.average_trade(portfolio) == (
        200 - 100 + 300
    ) / 3