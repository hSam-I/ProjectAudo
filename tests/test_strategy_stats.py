from app.analytics.strategy_stats import StrategyStats


def test_strategy_stats():

    stats = StrategyStats()

    stats.register_trade(50)

    stats.register_trade(-20)

    stats.register_trade(100)

    assert stats.trades == 3

    assert stats.wins == 2

    assert stats.losses == 1

    assert stats.win_rate == 2 / 3

    assert stats.loss_rate == 1 / 3