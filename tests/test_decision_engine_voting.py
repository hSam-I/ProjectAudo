"""
Covers Step 4 of the orphan-module integration: DecisionEngine._vote(),
which only runs when settings.enable_voting is True. Verifies that
voting combines multiple strategies' signals (weighted by
WeightManager, fed from persisted LearningEngine/PerformanceDatabase
stats via StrategyStats.from_persisted - the missing adapter flagged in
the integration plan), and that only the winning side's strategies end
up in Decision.contributing_strategies.

Also locks in that enable_voting=False (the default) and an explicitly
passed `strategy=` argument both bypass voting entirely, so existing
single-strategy callers are unaffected.
"""

import pandas as pd
import pytest

from app.config.settings import settings
from app.core.enums import Signal
from app.decision.decision_engine import DecisionEngine
from app.strategy.base_strategy import BaseStrategy


class AlwaysBuy(BaseStrategy):
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        return Signal.BUY


class AlwaysSell(BaseStrategy):
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        return Signal.SELL


class AlwaysHold(BaseStrategy):
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        return Signal.HOLD


@pytest.fixture
def isolated_performance_db(tmp_path, monkeypatch):

    from app.analytics.performance_db import PerformanceDatabase

    monkeypatch.setattr(
        PerformanceDatabase,
        "FILE",
        tmp_path / "strategy_stats.json",
    )

    return PerformanceDatabase


@pytest.fixture
def market_df():
    """
    Minimal df with every column DecisionEngine's non-strategy stages
    (SignalScorer, ScoreEngine, MarketRegimeDetector) read from, so
    evaluate() doesn't blow up on missing columns while we swap in
    fake strategies via get_strategy patching.
    """

    return pd.DataFrame(
        {
            "trend_market": [True],
            "bear_market": [False],
            "sideways_market": [False],
            "high_volatility_market": [False],
            "low_volatility_market": [False],
            "breakout": [False],

            "macd_bullish": [True],
            "volume_spike": [False],
            "hammer": [False],

            "ema_fast": [102],
            "ema_slow": [100],
            "adx": [30],
            "rsi": [60],
            "macd": [1],
            "macd_signal": [0.5],
        }
    )


def _patch_voting_strategies(monkeypatch, name_to_strategy: dict):
    """
    Patches app.decision.decision_engine.get_strategy so
    settings.voting_strategies names resolve to fixed fake strategies
    instead of the real registry, and points settings.voting_strategies
    at exactly those names. Falls back to the real registry for any
    other name, since DecisionEngine.__init__ always resolves
    settings.strategy ("ema_rsi" by default) even when voting is what
    actually drives evaluate().
    """

    from app.strategy.registry import get_strategy as real_get_strategy

    monkeypatch.setattr(settings, "voting_strategies", list(name_to_strategy))

    def fake_get_strategy(name):
        return name_to_strategy.get(name) or real_get_strategy(name)

    monkeypatch.setattr(
        "app.decision.decision_engine.get_strategy",
        fake_get_strategy,
    )


def test_voting_disabled_by_default_uses_single_strategy(market_df, monkeypatch):

    engine = DecisionEngine(strategy=AlwaysBuy())

    decision = engine.evaluate(market_df)

    assert decision.raw_signal == Signal.BUY
    assert decision.contributing_strategies == []


def test_voting_combines_multiple_strategies(isolated_performance_db, market_df, monkeypatch):

    monkeypatch.setattr(settings, "enable_voting", True)

    _patch_voting_strategies(
        monkeypatch,
        {
            "buyer_a": AlwaysBuy(),
            "buyer_b": AlwaysBuy(),
            "seller": AlwaysSell(),
        },
    )

    engine = DecisionEngine()

    decision = engine.evaluate(market_df)

    assert decision.raw_signal == Signal.BUY
    assert set(decision.contributing_strategies) == {"buyer_a", "buyer_b"}
    assert "seller" not in decision.contributing_strategies


def test_voting_weights_by_historical_win_rate(isolated_performance_db, market_df, monkeypatch):
    """
    With equal 1.0 weights this would be a 1-vs-1 tie -> HOLD. Giving
    the BUY voter a proven 90% win rate (weight 1.50 via WeightManager)
    is what breaks the tie in its favor - demonstrating that historical
    performance actually changes the outcome, not just the plumbing.
    """

    db = isolated_performance_db.load()
    db["strong_buyer"] = {"wins": 9, "losses": 1}
    isolated_performance_db.save(db)

    _patch_voting_strategies(
        monkeypatch,
        {
            "strong_buyer": AlwaysBuy(),
            "fresh_seller": AlwaysSell(),
        },
    )

    monkeypatch.setattr(settings, "enable_voting", True)

    engine = DecisionEngine()

    decision = engine.evaluate(market_df)

    assert decision.raw_signal == Signal.BUY
    assert decision.contributing_strategies == ["strong_buyer"]


def test_voting_tie_produces_hold_and_no_contributors(isolated_performance_db, market_df, monkeypatch):

    _patch_voting_strategies(
        monkeypatch,
        {
            "buyer": AlwaysBuy(),
            "seller": AlwaysSell(),
        },
    )

    monkeypatch.setattr(settings, "enable_voting", True)

    engine = DecisionEngine()

    decision = engine.evaluate(market_df)

    assert decision.raw_signal == Signal.HOLD
    assert decision.contributing_strategies == []


def test_explicit_strategy_bypasses_voting_even_when_enabled(isolated_performance_db, market_df, monkeypatch):

    monkeypatch.setattr(settings, "enable_voting", True)

    _patch_voting_strategies(
        monkeypatch,
        {"seller": AlwaysSell()},
    )

    engine = DecisionEngine(strategy=AlwaysBuy())

    decision = engine.evaluate(market_df)

    assert decision.raw_signal == Signal.BUY
    assert decision.contributing_strategies == []
