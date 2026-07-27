from app.reporting.average_trade import AverageTrade
from app.reporting.expectancy import Expectancy
from app.reporting.performance import Performance
from app.reporting.performance_report import PerformanceReport
from app.reporting.profit_factor import ProfitFactor


class ReportBuilder:
    """
    Builds a complete PerformanceReport.
    """

    @staticmethod
    def build(portfolio):

        gross_profit = sum(
            trade.profit
            for trade in portfolio.closed_trades
            if trade.profit > 0
        )

        gross_loss = abs(
            sum(
                trade.profit
                for trade in portfolio.closed_trades
                if trade.profit < 0
            )
        )

        net_profit = sum(
            trade.profit
            for trade in portfolio.closed_trades
        )

        return PerformanceReport(

            total_trades=Performance.total_trades(
                portfolio
            ),

            winning_trades=Performance.winning_trades(
                portfolio
            ),

            losing_trades=Performance.losing_trades(
                portfolio
            ),

            win_rate=Performance.win_rate(
                portfolio
            ),

            profit_factor=ProfitFactor.calculate(
                portfolio
            ),

            expectancy=Expectancy.calculate(
                portfolio
            ),

            average_win=AverageTrade.average_win(
                portfolio
            ),

            average_loss=AverageTrade.average_loss(
                portfolio
            ),

            average_trade=AverageTrade.average_trade(
                portfolio
            ),

            gross_profit=gross_profit,

            gross_loss=gross_loss,

            net_profit=net_profit,
        )