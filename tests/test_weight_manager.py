from app.analytics.strategy_stats import StrategyStats
from app.analytics.weight_manager import WeightManager


def test_high_weight():

    stats = StrategyStats()

    for _ in range(8):
        stats.register_trade(10)

    for _ in range(2):
        stats.register_trade(-5)

    assert WeightManager.weight(stats) == 1.50


def test_medium_weight():

    stats = StrategyStats()

    for _ in range(6):
        stats.register_trade(10)

    for _ in range(4):
        stats.register_trade(-5)

    assert WeightManager.weight(stats) == 1.25


def test_normal_weight():

    stats = StrategyStats()

    for _ in range(5):
        stats.register_trade(10)

    for _ in range(5):
        stats.register_trade(-5)

    assert WeightManager.weight(stats) == 1.00


def test_low_weight():

    stats = StrategyStats()

    for _ in range(3):
        stats.register_trade(10)

    for _ in range(7):
        stats.register_trade(-5)

    assert WeightManager.weight(stats) == 0.75