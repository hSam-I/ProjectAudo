from app.strategy.strategy_factory import StrategyFactory
from app.strategy.trend_following_strategy import (
    TrendFollowingStrategy,
)


def test_create_strategy():

    strategy = StrategyFactory.create(
        "trend_following"
    )

    assert isinstance(
        strategy,
        TrendFollowingStrategy,
    )


def test_available_strategies():

    names = StrategyFactory.available_strategies()

    assert "trend_following" in names
    assert "breakout" in names
    assert "mean_reversion" in names