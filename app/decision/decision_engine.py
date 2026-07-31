from dataclasses import dataclass

import pandas as pd

from app.ai.score_engine import ScoreEngine
from app.config.settings import settings
from app.core.enums import Signal
from app.decision.signal_filter import SignalFilter
from app.decision.signal_scorer import SignalScorer
from app.logging.logger import logger
from app.market.regime import MarketRegime
from app.market.regime_detector import MarketRegimeDetector
from app.strategy.base_strategy import BaseStrategy
from app.strategy.registry import get_strategy


@dataclass
class Decision:

    raw_signal: Signal

    signal: Signal

    score: int

    confidence: str

    reasons: list[str]

    regime: str


class DecisionEngine:

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

        raw_signal = self.strategy.generate_signal(df)

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
        )