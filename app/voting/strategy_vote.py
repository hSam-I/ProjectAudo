from dataclasses import dataclass

from app.core.enums import Signal


@dataclass
class StrategyVote:
    """
    Represents one strategy's vote.
    """

    strategy: str

    signal: Signal

    weight: float = 1.0