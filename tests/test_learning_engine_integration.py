"""
Covers Step 4 of the orphan-module integration end-to-end: with
settings.enable_voting=True, Backtester.run() must credit each closed
trade's profit/loss back to LearningEngine (persisted via
PerformanceDatabase), but only for the strategies that were on the
winning side of the vote that opened the trade
(Trade.contributing_strategies, set in DecisionEngine._vote and
threaded through by Backtester._register_learning).

Uses a single voting strategy (matching settings.strategy's default
"ema_rsi" behavior against the fixture data used elsewhere, e.g.
tests/test_backtester_costs.py) so the trade outcome is deterministic
and attributable to exactly one named strategy.
"""

from app.analytics.performance_db import PerformanceDatabase
from app.backtesting.backtester import Backtester
from app.config.settings import settings


def test_backtester_registers_learning_for_winning_strategy(
    random_walk_ohlcv, monkeypatch, tmp_path
):

    monkeypatch.setattr(
        PerformanceDatabase,
        "FILE",
        tmp_path / "strategy_stats.json",
    )

    monkeypatch.setattr(settings, "enable_voting", True)
    monkeypatch.setattr(settings, "voting_strategies", ["ema_rsi"])

    df = random_walk_ohlcv()

    portfolio = Backtester().run(df)

    assert portfolio.closed_trades_count > 0

    db = PerformanceDatabase.load()

    assert "ema_rsi" in db

    recorded = db["ema_rsi"]["wins"] + db["ema_rsi"]["losses"]

    assert recorded == portfolio.closed_trades_count


def test_backtester_skips_learning_when_voting_disabled(random_walk_ohlcv, monkeypatch, tmp_path):

    monkeypatch.setattr(
        PerformanceDatabase,
        "FILE",
        tmp_path / "strategy_stats.json",
    )

    df = random_walk_ohlcv()

    portfolio = Backtester().run(df)

    assert portfolio.closed_trades_count > 0

    db = PerformanceDatabase.load()

    assert db == {}
