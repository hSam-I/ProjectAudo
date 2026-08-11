import pandas as pd

from app.analytics.calmar_ratio import CalmarRatio
from app.analytics.sharpe_ratio import SharpeRatio
from app.analytics.sortino_ratio import SortinoRatio
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

            if peak == 0:
                drawdowns.append(0)
                continue

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

    def _period_returns(self):

        history = self.portfolio.balance_history

        if len(history) < 2:
            return []

        returns = []

        for i in range(1, len(history)):

            previous = history[i - 1]

            if previous == 0:
                returns.append(0.0)
                continue

            returns.append(
                (history[i] - previous) / previous
            )

        return returns

    def sharpe_ratio(self):

        return SharpeRatio.calculate(
            self._period_returns()
        )

    def sortino_ratio(self):

        return SortinoRatio.calculate(
            self._period_returns()
        )

    def cagr(self):
        """
        Compound annual growth rate, derived from the first trade's
        entry_time to the last closed trade's exit_time (not calendar
        "now" - backtests run over historical windows).
        """

        if not self.closed_trades:
            return 0.0

        start_time = pd.to_datetime(self.portfolio.trades[0].entry_time)
        end_time = pd.to_datetime(self.closed_trades[-1].exit_time)

        days = (end_time - start_time).days

        if days <= 0:
            return 0.0

        start_equity = self.portfolio.initial_balance
        end_equity = self.portfolio.balance

        if start_equity <= 0:
            return 0.0

        if end_equity <= 0:
            return -1.0

        return (end_equity / start_equity) ** (365 / days) - 1

    def calmar_ratio(self):

        return CalmarRatio.calculate(
            annual_return=self.cagr() * 100,
            max_drawdown=self.max_drawdown(),
        )