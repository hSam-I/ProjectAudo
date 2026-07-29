from dataclasses import dataclass


@dataclass
class StrategyStats:
    """
    Tracks strategy performance.
    """

    trades: int = 0
    wins: int = 0
    losses: int = 0

    def register_trade(self, profit: float):

        self.trades += 1

        if profit > 0:
            self.wins += 1
        else:
            self.losses += 1

    @property
    def win_rate(self) -> float:

        if self.trades == 0:
            return 0.0

        return self.wins / self.trades

    @property
    def loss_rate(self) -> float:

        if self.trades == 0:
            return 0.0

        return self.losses / self.trades