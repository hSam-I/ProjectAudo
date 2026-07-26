import plotly.graph_objects as go

from app.backtesting.portfolio import Portfolio


class DashboardCharts:

    @staticmethod
    def equity_curve(portfolio: Portfolio):

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                y=portfolio.balance_history,
                mode="lines",
                name="Equity",
            )
        )

        fig.update_layout(
            template="plotly_dark",
            title="Equity Curve",
            xaxis_title="Closed Trades",
            yaxis_title="Balance ($)",
            height=400,
        )

        return fig.to_html(
            full_html=False,
            include_plotlyjs="cdn",
        )

    @staticmethod
    def drawdown(portfolio: Portfolio):

        balances = portfolio.balance_history

        peak = balances[0]

        drawdowns = []

        for balance in balances:

            peak = max(peak, balance)

            drawdowns.append(
                ((balance - peak) / peak) * 100
            )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                y=drawdowns,
                fill="tozeroy",
                mode="lines",
                name="Drawdown",
            )
        )

        fig.update_layout(
            template="plotly_dark",
            title="Drawdown",
            xaxis_title="Closed Trades",
            yaxis_title="%",
            height=400,
        )

        return fig.to_html(
            full_html=False,
            include_plotlyjs=False,
        )