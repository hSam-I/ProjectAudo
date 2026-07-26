import plotly.graph_objects as go


def equity_chart(balance_history):

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=list(range(len(balance_history))),
            y=balance_history,
            mode="lines",
            name="Equity",
            line=dict(width=3),
        )
    )

    fig.update_layout(
        title="Equity Curve",
        template="plotly_dark",
        height=450,
        margin=dict(
            l=20,
            r=20,
            t=50,
            b=20,
        ),
        xaxis_title="Trades",
        yaxis_title="Balance ($)",
    )

    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
    )