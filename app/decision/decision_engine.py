from dataclasses import dataclass, field

import pandas as pd

from app.ai.score_engine import ScoreEngine
from app.analytics.performance_db import PerformanceDatabase
from app.analytics.strategy_stats import StrategyStats
from app.analytics.weight_manager import WeightManager
from app.config.settings import settings
from app.core.enums import Signal
from app.decision.signal_filter import SignalFilter
from app.decision.signal_scorer import SignalScorer
from app.logging.logger import logger
from app.market.regime import MarketRegime
from app.market.regime_detector import MarketRegimeDetector
from app.strategy.base_strategy import BaseStrategy
from app.strategy.registry import get_strategy
from app.voting.strategy_vote import StrategyVote
from app.voting.voting_engine import VotingEngine


@dataclass
class Decision:

    raw_signal: Signal

    signal: Signal

    score: int

    confidence: str

    reasons: list[str]

    regime: str

    contributing_strategies: list[str] = field(default_factory=list)


class DecisionEngine:

    def __init__(
        self,
        strategy: BaseStrategy | None = None,
    ):

        self._explicit_strategy = strategy

        self.strategy = strategy or get_strategy(
            settings.strategy
        )

    def _vote(
        self,
        df: pd.DataFrame,
    ) -> tuple[Signal, list[str]]:
        """
        Runs every settings.voting_strategies entry against df, weights
        each vote by that strategy's historical win rate (via
        WeightManager, fed from LearningEngine's persisted stats), and
        combines them with VotingEngine. Only strategies whose vote
        matches the winning side get returned as contributing_strategies -
        Backtester uses this to credit trade outcomes back to
        LearningEngine only for the strategies that "won" the vote, not
        every strategy that happened to vote BUY/SELL.
        """

        db = PerformanceDatabase.load()

        votes = []
        signals_by_strategy: dict[Signal, list[str]] = {}

        for strategy_name in settings.voting_strategies:

            strategy = get_strategy(strategy_name)

            signal = strategy.generate_signal(df)

            stats = StrategyStats.from_persisted(
                db.get(strategy_name)
            )

            weight = WeightManager.weight(stats)

            votes.append(
                StrategyVote(
                    strategy=strategy_name,
                    signal=signal,
                    weight=weight,
                )
            )

            signals_by_strategy.setdefault(
                signal, []
            ).append(strategy_name)

        combined_signal = VotingEngine.vote(votes)

        contributing_strategies = signals_by_strategy.get(
            combined_signal, []
        )

        return combined_signal, contributing_strategies

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> Decision:

        # ==================================================
        # MARKET REGIME
        # ==================================================

        try:

            regime = MarketRegimeDetector.detect(df)

        except Exception as e:

            logger.warning(
                f"Market Regime Detection Failed: {e}"
            )

            regime = MarketRegime.UNKNOWN

        # ==================================================
        # STRATEGY SIGNAL
        # ==================================================

        if (
            settings.enable_voting
            and self._explicit_strategy is None
        ):

            raw_signal, contributing_strategies = self._vote(df)

        else:

            raw_signal = self.strategy.generate_signal(df)

            contributing_strategies = []

        # ==================================================
        # LEGACY SCORE
        # ==================================================

        score, confidence, reasons = SignalScorer.score(df)

        # ==================================================
        # AI SCORE
        # ==================================================

        try:

            ai_score, ai_reasons = ScoreEngine.score(df)

            score += ai_score

            reasons.extend(ai_reasons)

        except Exception as e:

            logger.warning(
                f"AI Score Engine Failed: {e}"
            )

        # ==================================================
        # CLAMP
        # ==================================================

        score = max(
            -100,
            min(
                100,
                score,
            ),
        )

        # ==================================================
        # FILTER
        # ==================================================

        signal = SignalFilter.filter(
            raw_signal,
            score,
        )

        # ==================================================
        # RESULT
        # ==================================================

        regime_value = (
            regime.value
            if hasattr(regime, "value")
            else str(regime)
        )

        return Decision(
            raw_signal=raw_signal,
            signal=signal,
            score=score,
            confidence=confidence,
            reasons=reasons,
            regime=regime_value,
            contributing_strategies=contributing_strategies,
        )