import csv
from pathlib import Path

from app.backtesting.portfolio import Portfolio


class EquityReport:

    def __init__(self, filename: str = "equity_curve.csv"):

        Path("reports").mkdir(exist_ok=True)

        self.filepath = Path("reports") / filename

    def export(self, portfolio: Portfolio):

        with open(
            self.filepath,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.writer(file)

            writer.writerow(
                [
                    "Trade",
                    "Balance",
                ]
            )

            for i, balance in enumerate(
                portfolio.balance_history,
                start=0,
            ):

                writer.writerow(
                    [
                        i,
                        balance,
                    ]
                )