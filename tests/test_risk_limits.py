from app.backtesting.trade import Trade
from app.core.enums import OrderSide
from app.portfolio.portfolio_manager import PortfolioManager
from app.portfolio.risk_limits import RiskLimits


def test_risk_limits():

    portfolio = PortfolioManager()

    portfolio.register_trade(
        Trade(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            entry_price=100,
            quantity=1,
            entry_time="2026",
            stop_loss=95,
            take_profit=110,
            risk_amount=100,
        )
    )

    limits = RiskLimits(
        portfolio=portfolio,
        max_total_risk=200,
        max_positions=2,
    )

    assert limits.can_open_position(50)
    assert not limits.can_open_position(150)