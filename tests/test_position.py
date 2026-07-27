from app.backtesting.position import Position
from app.core.enums import PositionSide


def test_position_side():

    position = Position(
        symbol="BTCUSDT",
        side=PositionSide.LONG,
        quantity=1,
        entry_price=100,
        entry_time="1",
        stop_loss=90,
        take_profit=120,
        risk_amount=100,
    )

    assert position.is_long

    assert not position.is_short