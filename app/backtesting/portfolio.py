from app.backtesting.trade import Trade


class Portfolio:
    """
    Represents the trading account.

    Responsible for:

    - Balance
    - Open positions
    - Closed trades
    - Equity history
    """

    def __init__(self, initial_balance: float):

        self.initial_balance = initial_balance
        self.balance = initial_balance

        # Every trade ever created
        self.trades: list[Trade] = []

        # Currently open positions
        self.open_positions: list[Trade] = []

        # Closed trades
        self.closed_trades: list[Trade] = []

        # Equity Curve
        self.balance_history = [initial_balance]

    # --------------------------------------------------
    # OPEN POSITION
    # --------------------------------------------------

    def open_trade(self, trade: Trade) -> None:

        self.trades.append(trade)

        self.open_positions.append(trade)

    # --------------------------------------------------
    # CLOSE POSITION
    # --------------------------------------------------

    def close_trade(self, trade: Trade) -> None:

        self.balance += trade.profit

        if trade in self.open_positions:
            self.open_positions.remove(trade)

        if trade not in self.closed_trades:
            self.closed_trades.append(trade)

        self.balance_history.append(self.balance)

    # --------------------------------------------------
    # STATISTICS
    # --------------------------------------------------

    @property
    def total_trades(self) -> int:

        return len(self.trades)

    @property
    def open_trades(self) -> int:

        return len(self.open_positions)

    @property
    def closed_trades_count(self) -> int:

        return len(self.closed_trades)

    # --------------------------------------------------
    # HISTORY
    # --------------------------------------------------

    def trade_history(self) -> str:

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
                f"{trade.symbol} | "
                f"{trade.side} | "
                f"Entry: {trade.entry_price:.2f} | "
                f"Exit: {exit_price} | "
                f"Qty: {trade.quantity:.6f} | "
                f"Remaining: {trade.remaining_quantity:.6f} | "
                f"Risk: ${trade.risk_amount:.2f} | "
                f"Profit: {trade.profit:.2f} | "
                f"Reason: {trade.exit_reason} | "
                f"{trade.status}"
            )

        return "\n".join(lines)