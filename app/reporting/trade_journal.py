import csv
from pathlib import Path

from app.backtesting.portfolio import Portfolio


class TradeJournal:

    def __init__(self, filename: str = "trade_history.csv"):

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
                    "Symbol",
                    "Entry Time",
                    "Exit Time",
                    "Side",
                    "Entry",
                    "Exit",
                    "Quantity",
                    "Risk",
                    "Stop Loss",
                    "Take Profit",
                    "Profit",
                    "Reason",
                    "Status",
                ]
            )

            for trade in portfolio.trades:

                writer.writerow(
                    [
                        trade.symbol,
                        trade.entry_time,
                        trade.exit_time,
                        trade.side,
                        trade.entry_price,
                        trade.exit_price,
                        trade.quantity,
                        trade.risk_amount,
                        trade.stop_loss,
                        trade.take_profit,
                        trade.profit,
                        trade.exit_reason,
                        trade.status,
                    ]
                )