import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from pathlib import Path

from app.backtesting.performance import PerformanceAnalyzer
from app.backtesting.portfolio import Portfolio


class DrawdownChart:

    def __init__(self, filename: str = "drawdown.png"):

        Path("reports").mkdir(exist_ok=True)

        self.filepath = Path("reports") / filename

    def export(self, portfolio: Portfolio):

        performance = PerformanceAnalyzer(portfolio)

        drawdowns = performance.drawdown_series()

        plt.figure(figsize=(10, 5))

        plt.fill_between(
            range(len(drawdowns)),
            drawdowns,
            0,
        )

        plt.title("Drawdown")

        plt.xlabel("Closed Trades")

        plt.ylabel("Drawdown (%)")

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(self.filepath)

        plt.close()