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


def create_trade_with_times(profit: float, entry_time: str, exit_time: str):

    trade = Trade(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=100,
        quantity=1,
        entry_time=entry_time,

        stop_loss=95,
        take_profit=110,
        risk_amount=100,
    )

    trade.status = "CLOSED"
    trade.profit = profit
    trade.exit_time = exit_time

    return trade


def test_sharpe_ratio_uptrend_is_positive():

    portfolio = Portfolio(10000)
    portfolio.balance_history = [10000, 10100, 10250, 10400]

    analyzer = PerformanceAnalyzer(portfolio)

    assert analyzer.sharpe_ratio() > 0


def test_sharpe_ratio_insufficient_history_returns_zero():

    portfolio = Portfolio(10000)
    portfolio.balance_history = [10000]

    analyzer = PerformanceAnalyzer(portfolio)

    assert analyzer.sharpe_ratio() == 0.0


def test_sortino_ratio_no_downside_returns_infinite():

    portfolio = Portfolio(10000)
    portfolio.balance_history = [10000, 10100, 10250, 10400]

    analyzer = PerformanceAnalyzer(portfolio)

    assert analyzer.sortino_ratio() == float("inf")


def test_sortino_ratio_flat_history_returns_zero():

    portfolio = Portfolio(10000)
    portfolio.balance_history = [10000, 10000, 10000, 10000]

    analyzer = PerformanceAnalyzer(portfolio)

    assert analyzer.sortino_ratio() == 0.0


def test_sharpe_ratio_zero_variance_positive_mean_is_infinite():

    # Each step exactly doubles the balance, so every period return is
    # bit-for-bit 1.0 and the variance is exactly 0 (not just close to it).
    portfolio = Portfolio(10000)
    portfolio.balance_history = [10000, 20000, 40000, 80000]

    analyzer = PerformanceAnalyzer(portfolio)

    assert analyzer.sharpe_ratio() == float("inf")


def test_sharpe_ratio_flat_history_returns_zero():

    portfolio = Portfolio(10000)
    portfolio.balance_history = [10000, 10000, 10000, 10000]

    analyzer = PerformanceAnalyzer(portfolio)

    assert analyzer.sharpe_ratio() == 0.0


def test_cagr_doubling_over_one_year():

    portfolio = Portfolio(10000)

    trade = create_trade_with_times(10000, "2025-01-01", "2026-01-01")

    portfolio.trades = [trade]
    portfolio.closed_trades = [trade]
    portfolio.balance = 20000

    analyzer = PerformanceAnalyzer(portfolio)

    assert analyzer.cagr() == 1.0


def test_cagr_no_closed_trades_returns_zero():

    portfolio = Portfolio(10000)

    analyzer = PerformanceAnalyzer(portfolio)

    assert analyzer.cagr() == 0.0


def test_cagr_total_loss_returns_negative_one():

    portfolio = Portfolio(10000)

    trade = create_trade_with_times(-10000, "2025-01-01", "2026-01-01")

    portfolio.trades = [trade]
    portfolio.closed_trades = [trade]
    portfolio.balance = 0

    analyzer = PerformanceAnalyzer(portfolio)

    assert analyzer.cagr() == -1.0


def test_calmar_ratio_combines_cagr_and_drawdown():

    portfolio = Portfolio(10000)

    trade = create_trade_with_times(10000, "2025-01-01", "2026-01-01")

    portfolio.trades = [trade]
    portfolio.closed_trades = [trade]
    portfolio.balance = 20000
    portfolio.balance_history = [10000, 8000, 20000]

    analyzer = PerformanceAnalyzer(portfolio)

    assert analyzer.calmar_ratio() == 5.0
