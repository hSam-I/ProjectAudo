from app.strategy.strategy_factory import (
    StrategyFactory,
)


def test_strategy_factory():

    strategy = StrategyFactory.create(
        {
            "ema_fast": 10,
            "ema_slow": 30,
            "rsi_buy": 60,
            "rsi_sell": 40,
        }
    )

    assert strategy.ema_fast == 10
    assert strategy.ema_slow == 30

    assert strategy.rsi_buy == 60
    assert strategy.rsi_sell == 40