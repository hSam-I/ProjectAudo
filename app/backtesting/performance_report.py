from app.backtesting.performance import PerformanceAnalyzer
from app.backtesting.portfolio import Portfolio


class PerformanceReport:
    """
    Generates a performance report.
    """

    @staticmethod
    def generate(trades):

        portfolio = Portfolio(initial_balance=10000)

        portfolio.trades = trades
        portfolio.balance_history = [10000]

        analyzer = PerformanceAnalyzer(portfolio)

        return {
    "total_trades": len(analyzer.closed_trades),
    "winning_trades": len(analyzer.winning_trades),
    "losing_trades": len(analyzer.losing_trades),

    "gross_profit": round(analyzer.gross_profit(), 2),
    "gross_loss": round(analyzer.gross_loss(), 2),

    "net_profit": round(
        analyzer.gross_profit()
        - analyzer.gross_loss(),
        2,
    ),

    "win_rate": round(analyzer.win_rate(), 2),
    "loss_rate": round(analyzer.loss_rate(), 2),

    "average_win": round(analyzer.average_win(), 2),
    "average_loss": round(analyzer.average_loss(), 2),

    "largest_win": round(analyzer.largest_win(), 2),
    "largest_loss": round(analyzer.largest_loss(), 2),

    "profit_factor": round(analyzer.profit_factor(), 2),
    "expectancy": round(analyzer.expectancy(), 2),

    "max_drawdown": round(analyzer.max_drawdown(), 2),
}