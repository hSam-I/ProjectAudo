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


def signal_distribution_chart(decisions: list[dict]):
    """
    Bar chart of final-signal counts over the recent decisions the live
    loop logged. Handles an empty `decisions` list explicitly (single
    "No data" bar at zero) rather than letting an empty Bar trace
    render blank - same defensive spirit as TradeDistributionChart's
    zero-trade handling.
    """

    counts: dict[str, int] = {}

    for entry in decisions:
        signal = entry.get("signal", "UNKNOWN")
        counts[signal] = counts.get(signal, 0) + 1

    labels = list(counts.keys()) if counts else ["No data"]
    values = list(counts.values()) if counts else [0]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=labels,
            y=values,
            name="Signals",
        )
    )

    fig.update_layout(
        title="Signal Distribution (recent decisions)",
        template="plotly_dark",
        height=350,
        margin=dict(
            l=20,
            r=20,
            t=50,
            b=20,
        ),
        xaxis_title="Signal",
        yaxis_title="Count",
    )

    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
    )