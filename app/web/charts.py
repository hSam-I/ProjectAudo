import plotly.graph_objects as go

from app.decision.signal_filter import SignalFilter

# Plotly's own "plotly_dark" template's chart background (rgb(17,17,17))
# - used as the marker-ring color below, matching the surface the chart
# actually renders on rather than an unrelated design-system default.
_DARK_CHART_SURFACE = "#111111"

# Status-palette steps (validated dataviz reference palette): candle
# direction is a polarity that genuinely means good/bad for a paper
# trader (price up vs down), so it wears status tokens rather than a
# categorical hue - see candlestick_chart().
_STATUS_GOOD = "#0ca30c"
_STATUS_CRITICAL = "#d03b3b"
_MUTED_INK = "#898781"

# Categorical slots 1 (blue) and 5 (magenta): BUY/SELL marker identity
# is a different "job" than candle direction (which decision fired, not
# whether it was good or bad), so it wears categorical hues - chosen to
# not collide with the status green/red used for the candles themselves.
_CATEGORICAL_BUY = "#3987e5"
_CATEGORICAL_SELL = "#d55181"


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


def _empty_chart_fallback(title: str, message: str, height: int) -> str:
    """
    Shared "nothing to plot yet" state for candlestick_chart()/score_chart() -
    an annotation on an axis-less figure rather than a blank trace,
    same defensive spirit as signal_distribution_chart()'s "No data" bar.
    """

    fig = go.Figure()

    fig.add_annotation(
        text=message,
        showarrow=False,
        font=dict(size=14, color=_MUTED_INK),
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
    )

    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=height,
        margin=dict(
            l=20,
            r=20,
            t=50,
            b=20,
        ),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
    )


def candlestick_chart(decisions: list[dict]) -> str:
    """
    Candlestick price chart with BUY/SELL decision markers overlaid.
    `decisions` must be chronological (oldest first - see
    app/web/live_status_data.py::_chart_decisions()).

    Entries written before OHLC existed on LiveDecisionLog lack the
    open/high/low/close keys entirely - they're filtered out rather
    than assumed present, so a history mixing old (no price) and new
    (priced) entries never crashes, it just draws candles where price
    data exists. If NONE do (right after upgrading), falls back to an
    explicit "no data" state instead of an empty/broken chart.

    HOLD decisions are never marked - they're the overwhelming majority
    of entries, and marking them would bury the rare BUY/SELL signals
    under a field of dots. A third, muted trace marks decisions where
    the raw signal was BUY/SELL but SignalFilter downgraded it to HOLD
    (score below threshold) - the moments the score_chart()'s threshold
    line explains.
    """

    candles = [
        entry
        for entry in decisions
        if all(
            isinstance(entry.get(key), (int, float))
            for key in ("open", "high", "low", "close")
        )
    ]

    if not candles:
        return _empty_chart_fallback(
            "Price & Signals",
            "No price data logged yet",
            500,
        )

    highs = [entry["high"] for entry in candles]
    lows = [entry["low"] for entry in candles]

    price_span = max(highs) - min(lows)
    offset = price_span * 0.02 if price_span > 0 else 1.0

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=[entry["timestamp"] for entry in candles],
            open=[entry["open"] for entry in candles],
            high=highs,
            low=lows,
            close=[entry["close"] for entry in candles],
            name="Price",
            increasing_line_color=_STATUS_GOOD,
            decreasing_line_color=_STATUS_CRITICAL,
        )
    )

    buys = [entry for entry in candles if entry.get("signal") == "BUY"]
    sells = [entry for entry in candles if entry.get("signal") == "SELL"]

    filtered = [
        entry
        for entry in candles
        if entry.get("signal") == "HOLD"
        and entry.get("raw_signal") not in (None, "HOLD")
    ]

    if buys:

        fig.add_trace(
            go.Scatter(
                x=[entry["timestamp"] for entry in buys],
                y=[entry["low"] - offset for entry in buys],
                mode="markers",
                name="BUY",
                marker=dict(
                    symbol="triangle-up",
                    size=12,
                    color=_CATEGORICAL_BUY,
                    line=dict(width=2, color=_DARK_CHART_SURFACE),
                ),
                customdata=[entry.get("score") for entry in buys],
                hovertemplate="%{x}<br>BUY | score=%{customdata}<extra></extra>",
            )
        )

    if sells:

        fig.add_trace(
            go.Scatter(
                x=[entry["timestamp"] for entry in sells],
                y=[entry["high"] + offset for entry in sells],
                mode="markers",
                name="SELL",
                marker=dict(
                    symbol="triangle-down",
                    size=12,
                    color=_CATEGORICAL_SELL,
                    line=dict(width=2, color=_DARK_CHART_SURFACE),
                ),
                customdata=[entry.get("score") for entry in sells],
                hovertemplate="%{x}<br>SELL | score=%{customdata}<extra></extra>",
            )
        )

    if filtered:

        fig.add_trace(
            go.Scatter(
                x=[entry["timestamp"] for entry in filtered],
                y=[entry["close"] for entry in filtered],
                mode="markers",
                name="Filtered",
                marker=dict(
                    symbol="circle-open",
                    size=8,
                    color=_MUTED_INK,
                    opacity=0.7,
                ),
                customdata=[entry.get("raw_signal") for entry in filtered],
                hovertemplate="%{x}<br>filtered (raw=%{customdata})<extra></extra>",
            )
        )

    fig.update_layout(
        title="Price & Signals",
        template="plotly_dark",
        height=500,
        margin=dict(
            l=20,
            r=20,
            t=50,
            b=20,
        ),
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
    )

    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
    )


def score_chart(decisions: list[dict]) -> str:
    """
    Score time series with SignalFilter's threshold line overlaid, so
    it's easy to spot decisions that narrowly missed being acted on.
    `decisions` must be chronological (oldest first).

    Reuses SignalFilter.BUY_THRESHOLD rather than duplicating the
    magic number 60 - BUY_THRESHOLD and SELL_THRESHOLD are equal today
    and both gate on `score >= threshold`, so a single reference line
    covers both directions. If they ever diverge, this needs a second
    add_hline() for SELL_THRESHOLD.
    """

    points = [
        entry
        for entry in decisions
        if isinstance(entry.get("score"), (int, float))
    ]

    if not points:
        return _empty_chart_fallback(
            "Decision Score",
            "No decisions logged yet",
            350,
        )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=[entry["timestamp"] for entry in points],
            y=[entry["score"] for entry in points],
            mode="lines+markers",
            name="Score",
            line=dict(
                width=2,
                color=_CATEGORICAL_BUY,
            ),
            marker=dict(size=8),
        )
    )

    fig.add_hline(
        y=SignalFilter.BUY_THRESHOLD,
        line_dash="dash",
        line_color=_MUTED_INK,
        annotation_text=f"Filter threshold ({SignalFilter.BUY_THRESHOLD})",
        annotation_position="top left",
    )

    fig.update_layout(
        title="Decision Score",
        template="plotly_dark",
        height=350,
        margin=dict(
            l=20,
            r=20,
            t=50,
            b=20,
        ),
        xaxis_title="Time",
        yaxis_title="Score",
        yaxis=dict(
            range=[-105, 105],
            dtick=25,
        ),
        hovermode="x unified",
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