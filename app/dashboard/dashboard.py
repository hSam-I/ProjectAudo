from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.backtesting.performance import PerformanceAnalyzer
from app.backtesting.portfolio import Portfolio
from app.dashboard.charts import DashboardCharts


class Dashboard:

    def __init__(self):

        self.template_path = Path(
            "app/dashboard/templates"
        )

        self.output_path = Path(
            "reports/dashboard.html"
        )

        self.environment = Environment(
            loader=FileSystemLoader(
                self.template_path
            )
        )

    def export(self, portfolio: Portfolio):

        performance = PerformanceAnalyzer(
            portfolio
        )

        template = self.environment.get_template(
            "report.html"
        )

        html = template.render(

            balance=portfolio.balance,

            total_trades=portfolio.total_trades,

            closed_trades=portfolio.closed_trades,

            open_trades=portfolio.open_trades,

            win_rate=performance.win_rate(),

            loss_rate=performance.loss_rate(),

            profit_factor=performance.profit_factor(),

            expectancy=performance.expectancy(),

            max_drawdown=performance.max_drawdown(),

            equity_chart=DashboardCharts.equity_curve(
                portfolio
            ),

            drawdown_chart=DashboardCharts.drawdown(
                portfolio
            ),

            trade_history=portfolio.trades,

        )

        self.output_path.write_text(
            html,
            encoding="utf-8",
        )