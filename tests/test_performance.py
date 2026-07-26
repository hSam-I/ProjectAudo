from app.backtesting.performance import PerformanceAnalyzer
from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade


def create_trade(profit: float):

    trade = Trade(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=100,
        quantity=1,
        entry_time="2026",

        stop_loss=95,
        take_profit=110,
        risk_amount=100,
    )

    trade.status = "CLOSED"
    trade.profit = profit

    return trade


def test_win_rate():

    portfolio = Portfolio(10000)

    portfolio.trades = [
        create_trade(100),
        create_trade(-100),
        create_trade(200),
    ]

    analyzer = PerformanceAnalyzer(portfolio)

    assert analyzer.win_rate() == (2 / 3) * 100


def test_profit_factor():

    portfolio = Portfolio(10000)

    portfolio.trades = [
        create_trade(200),
        create_trade(-100),
    ]

    analyzer = PerformanceAnalyzer(portfolio)

    assert analyzer.profit_factor() == 2.0


def test_expectancy():

    portfolio = Portfolio(10000)

    portfolio.trades = [
        create_trade(200),
        create_trade(-100),
    ]

    analyzer = PerformanceAnalyzer(portfolio)

    expectancy = analyzer.expectancy()

    assert expectancy > 0
    