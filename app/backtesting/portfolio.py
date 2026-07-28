from app.backtesting.trade import Trade


class Portfolio:
    """
    Stores trades and account balance.

    Also keeps historical balance values
    for performance analysis.
    """

    def __init__(self, initial_balance: float):

        self.initial_balance = initial_balance
        self.balance = initial_balance

        self.trades: list[Trade] = []

        self.closed_trades: list[Trade] = []

        self.balance_history = [initial_balance]

    def open_trade(self, trade: Trade):

        self.trades.append(trade)

    def close_trade(self, trade: Trade):

        self.balance += trade.profit

        if trade not in self.closed_trades:
            self.closed_trades.append(trade)

        self.balance_history.append(self.balance)

    @property
    def total_trades(self):

        return len(self.trades)

    @property
    def closed_trades_count(self):

        return len(self.closed_trades)

    @property
    def open_trades(self):

        return [
            trade
            for trade in self.trades
            if trade.status == "OPEN"
        ]

    @property
    def open_trades_count(self):

        return len(self.open_trades)

    def trade_history(self):

        if not self.trades:
            return "No trades."

        lines = []

        for i, trade in enumerate(self.trades, start=1):

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
                f"Qty: {trade.quantity:.6f} | "
                f"Risk: ${trade.risk_amount:.2f} | "
                f"Profit: {trade.profit:.2f} | "
                f"Reason: {trade.exit_reason} | "
                f"{trade.status}"
            )

        return "\n".join(lines)