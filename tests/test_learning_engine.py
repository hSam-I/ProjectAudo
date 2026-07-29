from app.analytics.learning_engine import LearningEngine
from app.analytics.performance_db import PerformanceDatabase


def test_learning_engine(tmp_path):

    PerformanceDatabase.FILE = tmp_path / "stats.json"

    LearningEngine.register_trade(
        strategy_name="ema_rsi",
        profit=100,
    )

    LearningEngine.register_trade(
        strategy_name="ema_rsi",
        profit=-50,
    )

    db = PerformanceDatabase.load()

    assert db["ema_rsi"]["wins"] == 1
    assert db["ema_rsi"]["losses"] == 1