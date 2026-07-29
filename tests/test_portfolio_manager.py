from app.backtesting.trade import Trade
from app.core.enums import OrderSide
from app.portfolio.portfolio_manager import PortfolioManager


def test_portfolio_manager():

    manager = PortfolioManager()

    trade = Trade(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        entry_price=100,
        quantity=1,
        entry_time="2026-01-01 00:00:00",
        stop_loss=95,
        take_profit=110,
        risk_amount=100,
    )

    assert manager.can_open_trade("BTCUSDT")

    manager.register_trade(trade)

    assert manager.has_position("BTCUSDT")
    assert manager.count() == 1
    assert manager.get_position("BTCUSDT") == trade

    assert manager.total_exposure() == 100

    manager.close_trade(trade)

    assert not manager.has_position("BTCUSDT")
    assert manager.count() == 0