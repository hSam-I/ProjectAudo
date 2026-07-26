from app.backtesting.portfolio import Portfolio


class PerformanceAnalyzer:

    def __init__(self, portfolio: Portfolio):

        self.portfolio = portfolio

    @property
    def closed_trades(self):

        return [
            trade
            for trade in self.portfolio.trades
            if trade.status == "CLOSED"
        ]

    @property
    def winning_trades(self):

        return [
            trade
            for trade in self.closed_trades
            if trade.profit > 0
        ]

    @property
    def losing_trades(self):

        return [
            trade
            for trade in self.closed_trades
            if trade.profit <= 0
        ]

    def win_rate(self):

        if not self.closed_trades:
            return 0

        return (
            len(self.winning_trades)
            / len(self.closed_trades)
        ) * 100

    def loss_rate(self):

        if not self.closed_trades:
            return 0

        return (
            len(self.losing_trades)
            / len(self.closed_trades)
        ) * 100

    def average_win(self):

        if not self.winning_trades:
            return 0

        return sum(
            trade.profit
            for trade in self.winning_trades
        ) / len(self.winning_trades)

    def average_loss(self):

        if not self.losing_trades:
            return 0

        return sum(
            trade.profit
            for trade in self.losing_trades
        ) / len(self.losing_trades)

    def largest_win(self):

        if not self.winning_trades:
            return 0

        return max(
            trade.profit
            for trade in self.winning_trades
        )

    def largest_loss(self):

        if not self.losing_trades:
            return 0

        return min(
            trade.profit
            for trade in self.losing_trades
        )

    def gross_profit(self):

        return sum(
            trade.profit
            for trade in self.winning_trades
        )

    def gross_loss(self):

        return abs(
            sum(
                trade.profit
                for trade in self.losing_trades
            )
        )

    def profit_factor(self):

        gross_loss = self.gross_loss()

        if gross_loss == 0:
            return 0

        return self.gross_profit() / gross_loss

    def expectancy(self):

        if not self.closed_trades:
            return 0

        return sum(
            trade.profit
            for trade in self.closed_trades
        ) / len(self.closed_trades)

    def peak_equity(self):

        if not self.portfolio.balance_history:
            return self.portfolio.initial_balance

        return max(self.portfolio.balance_history)

    def drawdown_series(self):

        if not self.portfolio.balance_history:
            return []

        peak = self.portfolio.balance_history[0]

        drawdowns = []

        for balance in self.portfolio.balance_history:

            peak = max(peak, balance)

            drawdown = (
                (balance - peak)
                / peak
            ) * 100

            drawdowns.append(drawdown)

        return drawdowns

    def max_drawdown(self):

        drawdowns = self.drawdown_series()

        if not drawdowns:
            return 0

        return abs(min(drawdowns))