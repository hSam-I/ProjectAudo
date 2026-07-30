from dataclasses import dataclass

import pandas as pd

from app.ai.score_engine import ScoreEngine
from app.config.settings import settings
from app.core.enums import Signal
from app.decision.signal_filter import SignalFilter
from app.decision.signal_scorer import SignalScorer
from app.market.regime import MarketRegime
from app.market.regime_detector import MarketRegimeDetector
from app.strategy.base_strategy import BaseStrategy
from app.strategy.registry import get_strategy


@dataclass
class Decision:
    """
    Decision object returned by DecisionEngine.
    """

    raw_signal: Signal
    signal: Signal

    score: int

    confidence: str

    reasons: list[str]

    regime: str


class DecisionEngine:
    """
    Central AI Decision Engine.

    Keeps backward compatibility while extending
    the architecture with:

    - Market Regime Detection
    - AI Feature Scoring
    - Signal Scoring
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

        # -----------------------------
        # Market Regime
        # -----------------------------

        try:
            regime = MarketRegimeDetector.detect(df)
        except Exception:
            regime = MarketRegime.UNKNOWN

        # -----------------------------
        # Strategy Signal
        # -----------------------------

        raw_signal = self.strategy.generate_signal(df)

        # -----------------------------
        # Legacy Score
        # -----------------------------

        score, confidence, reasons = SignalScorer.score(df)

        # -----------------------------
        # AI Score
        # -----------------------------

        try:

            ai_score, ai_reasons = ScoreEngine.score(df)

            score += ai_score

            reasons.extend(ai_reasons)

        except Exception:
            pass

        # -----------------------------
        # Clamp score
        # -----------------------------

        score = max(-100, min(100, score))

        # -----------------------------
        # Final Signal
        # -----------------------------

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
            regime=regime.value,
        )