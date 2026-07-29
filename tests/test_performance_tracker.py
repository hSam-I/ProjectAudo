from app.backtesting.trade import Trade
from app.core.enums import OrderSide
from app.portfolio.performance_tracker import PerformanceTracker
from app.portfolio.portfolio_manager import PortfolioManager


def test_performance_tracker():

    portfolio = PortfolioManager()

    trade = Trade(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        entry_price=100,
        quantity=2,
        entry_time="2026-01-01",
        stop_loss=95,
        take_profit=110,
        risk_amount=100,
    )

    portfolio.register_trade(trade)

    tracker = PerformanceTracker(portfolio)

    assert tracker.positions() == 1
    assert tracker.exposure() == 200
    assert tracker.has_open_positions()