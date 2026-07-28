from app.backtesting.trade import Trade
from app.core.enums import OrderSide
from app.risk.position_manager import PositionManager


def test_position_manager_moves_stop_to_break_even():

    trade = Trade(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        entry_price=100,
        quantity=1,
        entry_time="1",
        stop_loss=95,
        take_profit=120,
        risk_amount=100,
    )

    PositionManager.update(
        trade=trade,
        current_price=103,
        atr=2,
    )

    assert trade.stop_loss >= 100