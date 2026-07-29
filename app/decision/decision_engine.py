from dataclasses import dataclass

import pandas as pd

from app.ai.strategy_selector import StrategySelector
from app.config.settings import settings
from app.core.enums import Signal
from app.decision.signal_filter import SignalFilter
from app.decision.signal_scorer import SignalScorer
from app.strategy.base_strategy import BaseStrategy
from app.strategy.registry import get_strategy


@dataclass
class Decision:
    """
    Result of the decision pipeline.
    """

    raw_signal: Signal
    signal: Signal

    score: int
    confidence: str

    reasons: list[str]


class DecisionEngine:
    """
    Central decision pipeline.

    Market Regime
        ↓
    Strategy Selector
        ↓
    Strategy
        ↓
    Signal Scorer
        ↓
    Signal Filter
    """

    def __init__(
        self,
        strategy: BaseStrategy | None = None,
    ):

        self.strategy = strategy or get_strategy(
            settings.strategy
        )

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> Decision:

        # Automatically choose the best strategy
        strategy_name = StrategySelector.choose(df)

        self.strategy = get_strategy(strategy_name)

        raw_signal = self.strategy.generate_signal(df)

        score, confidence, reasons = SignalScorer.score(
            df
        )

        signal = SignalFilter.filter(
            raw_signal,
            score,
        )

        return Decision(
            raw_signal=raw_signal,
            signal=signal,
            score=score,
            confidence=confidence,
            reasons=reasons,
        )