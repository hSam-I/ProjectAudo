from app.backtesting.trade import Trade


class Portfolio:

    def __init__(self, initial_balance: float):

        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.trades: list[Trade] = []

    def open_trade(self, trade: Trade):

        self.trades.append(trade)

    def close_trade(self, trade: Trade):

        self.balance += trade.profit

    @property
    def total_trades(self):

        return len(self.trades)

    @property
    def closed_trades(self):

        return len(
            [trade for trade in self.trades if not trade.is_open]
        )

    @property
    def open_trades(self):

        return len(
            [trade for trade in self.trades if trade.is_open]
        )

    def trade_history(self):

        if len(self.trades) == 0:
            return "No trades."

        lines = []

        for i, trade in enumerate(self.trades, start=1):

            status = "OPEN" if trade.is_open else "CLOSED"

            exit_price = (
                "-"
                if trade.exit_price is None
                else f"{trade.exit_price:.2f}"
            )

            lines.append(
                f"{i}. "
                f"{trade.side} | "
                f"Entry: {trade.entry_price:.2f} | "
                f"Exit: {exit_price} | "
                f"Profit: {trade.profit:.2f} | "
                f"{status}"
            )

        return "\n".join(lines)