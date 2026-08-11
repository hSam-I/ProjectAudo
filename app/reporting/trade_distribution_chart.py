import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from pathlib import Path

from app.backtesting.portfolio import Portfolio


class TradeDistributionChart:

    def __init__(self, filename: str = "trade_distribution.png"):

        Path("reports").mkdir(exist_ok=True)

        self.filepath = Path("reports") / filename

    def export(self, portfolio: Portfolio):

        wins = len(
            [
                trade
                for trade in portfolio.trades
                if trade.profit > 0
            ]
        )

        losses = len(
            [
                trade
                for trade in portfolio.trades
                if trade.profit <= 0
            ]
        )

        plt.figure(figsize=(6, 6))

        if wins == 0 and losses == 0:

            plt.text(
                0.5,
                0.5,
                "No trades",
                ha="center",
                va="center",
            )

            plt.axis("off")

        else:

            plt.pie(
                [wins, losses],
                labels=["Wins", "Losses"],
                autopct="%1.1f%%",
            )

        plt.title("Trade Distribution")

        plt.tight_layout()

        plt.savefig(self.filepath)

        plt.close()