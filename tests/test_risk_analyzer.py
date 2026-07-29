from app.backtesting.trade import Trade
from app.core.enums import OrderSide
from app.portfolio.portfolio_manager import PortfolioManager
from app.portfolio.risk_analyzer import RiskAnalyzer


def test_risk_analyzer():

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

    portfolio.register_trade(
        Trade(
            symbol="ETHUSDT",
            side=OrderSide.BUY,
            entry_price=200,
            quantity=1,
            entry_time="2026",
            stop_loss=190,
            take_profit=220,
            risk_amount=50,
        )
    )

    analyzer = RiskAnalyzer(portfolio)

    assert analyzer.total_risk() == 150
    assert analyzer.average_risk() == 75
    assert analyzer.max_risk() == 100