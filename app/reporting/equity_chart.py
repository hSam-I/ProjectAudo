import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from pathlib import Path

from app.backtesting.portfolio import Portfolio


class EquityChart:

    def __init__(self, filename: str = "equity_curve.png"):

        Path("reports").mkdir(exist_ok=True)

        self.filepath = Path("reports") / filename

    def export(self, portfolio: Portfolio):

        plt.figure(figsize=(10, 5))

        plt.plot(
            portfolio.balance_history,
            linewidth=2,
        )

        plt.title("Equity Curve")

        plt.xlabel("Closed Trades")

        plt.ylabel("Balance ($)")

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(self.filepath)

        plt.close()