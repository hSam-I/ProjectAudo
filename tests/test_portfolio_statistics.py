from app.backtesting.trade import Trade
from app.core.enums import OrderSide
from app.portfolio.portfolio_manager import PortfolioManager
from app.portfolio.statistics import PortfolioStatistics


def test_portfolio_statistics():

    portfolio = PortfolioManager()

    portfolio.register_trade(
        Trade(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            entry_price=100,
            quantity=2,
            entry_time="2026",
            stop_loss=95,
            take_profit=110,
            risk_amount=100,
        )
    )

    portfolio.register_trade(
        Trade(
            symbol="ETHUSDT",
            side=OrderSide.BUY,
            entry_price=200,
            quantity=1,
            entry_time="2026",
            stop_loss=190,
            take_profit=220,
            risk_amount=100,
        )
    )

    stats = PortfolioStatistics(portfolio)

    assert stats.positions() == 2
    assert stats.exposure() == 400
    assert stats.average_position_size() == 200