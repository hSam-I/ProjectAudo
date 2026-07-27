from app.strategy.breakout_strategy import BreakoutStrategy
from app.strategy.ema_rsi_strategy import EMARSIStrategy


def test_strategy_metadata():

    ema = EMARSIStrategy()

    breakout = BreakoutStrategy()

    assert ema.name == "ema_rsi"
    assert breakout.name == "breakout"

    assert isinstance(ema.description, str)
    assert isinstance(breakout.description, str)

    assert ema.version == "1.0"
    assert breakout.version == "1.0"