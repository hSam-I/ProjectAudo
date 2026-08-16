"""
Covers app.web.charts - the Plotly HTML-fragment builders behind the
dashboard (/) and live-status (/live) pages. This is the first direct
test coverage of this module (previously only exercised indirectly
through tests/test_web_server.py's page-render tests) - candlestick_chart()
and score_chart() have real branching logic (OHLC filtering for
backward-compatible decisions.jsonl entries, empty-data fallbacks,
signal separation, a threshold line) worth pinning directly.
"""

from app.decision.signal_filter import SignalFilter
from app.web.charts import (
    candlestick_chart,
    score_chart,
    signal_distribution_chart,
)


def _entry(timestamp, signal="HOLD", raw_signal=None, score=0, candle=None):

    entry = {
        "timestamp": timestamp,
        "symbol": "BTC/USDT",
        "raw_signal": raw_signal if raw_signal is not None else signal,
        "signal": signal,
        "score": score,
        "regime": "RANGING",
    }

    if candle is not None:
        entry.update(candle)

    return entry


def _candle(open_=100.0, high=105.0, low=95.0, close=102.0):
    return {"open": open_, "high": high, "low": low, "close": close}


# ---------------------------------------------------------------------
# candlestick_chart
# ---------------------------------------------------------------------


def test_candlestick_chart_renders_from_entries_with_ohlc():

    decisions = [
        _entry("2024-01-01 00:00:00", candle=_candle(close=101.0)),
        _entry("2024-01-01 01:00:00", candle=_candle(close=103.0)),
    ]

    html = candlestick_chart(decisions)

    assert "Price &amp; Signals" in html or "Price & Signals" in html
    assert "No price data logged yet" not in html


def test_candlestick_chart_ignores_entries_without_ohlc():
    """
    Backward-compat lock: entries written before OHLC existed on
    LiveDecisionLog lack the open/high/low/close keys entirely - mixed
    old+new history must not crash, and only the priced entries plot.
    """

    decisions = [
        _entry("2024-01-01 00:00:00", score=1),  # old format, no candle
        _entry("2024-01-01 01:00:00", score=2),  # old format, no candle
        _entry("2024-01-01 02:00:00", score=3, candle=_candle()),
    ]

    html = candlestick_chart(decisions)

    assert "No price data logged yet" not in html


def test_candlestick_chart_falls_back_when_no_entry_has_ohlc():
    """
    The real state right after upgrading to this feature: every
    existing decisions.jsonl entry lacks OHLC. Must not crash.
    """

    decisions = [
        _entry("2024-01-01 00:00:00", score=1),
        _entry("2024-01-01 01:00:00", score=2),
    ]

    html = candlestick_chart(decisions)

    assert "No price data logged yet" in html


def test_candlestick_chart_handles_an_empty_decision_list():

    html = candlestick_chart([])

    assert "No price data logged yet" in html


def test_candlestick_chart_omits_hold_markers():

    decisions = [
        _entry("2024-01-01 00:00:00", signal="HOLD", candle=_candle()),
    ]

    html = candlestick_chart(decisions)

    assert '"name":"BUY"' not in html.replace(" ", "")
    assert '"name":"SELL"' not in html.replace(" ", "")


def test_candlestick_chart_marks_buy_and_sell_separately():

    decisions = [
        _entry("2024-01-01 00:00:00", signal="BUY", candle=_candle()),
        _entry("2024-01-01 01:00:00", signal="SELL", candle=_candle()),
    ]

    html = candlestick_chart(decisions)

    compact = html.replace(" ", "")

    assert '"name":"BUY"' in compact
    assert '"name":"SELL"' in compact


def test_candlestick_chart_marks_filtered_decisions():
    """
    A decision whose raw_signal was BUY/SELL but whose final signal was
    downgraded to HOLD by SignalFilter (score below threshold) gets its
    own muted "Filtered" trace - the moment score_chart()'s threshold
    line explains.
    """

    decisions = [
        _entry(
            "2024-01-01 00:00:00",
            signal="HOLD",
            raw_signal="BUY",
            candle=_candle(),
        ),
    ]

    html = candlestick_chart(decisions)

    assert '"name":"Filtered"' in html.replace(" ", "")


def test_candlestick_chart_hides_the_rangeslider():

    decisions = [_entry("2024-01-01 00:00:00", candle=_candle())]

    html = candlestick_chart(decisions)

    assert '"rangeslider":{"visible":false}' in html.replace(" ", "")


# ---------------------------------------------------------------------
# score_chart
# ---------------------------------------------------------------------


def test_score_chart_includes_the_filter_threshold_line():

    decisions = [_entry("2024-01-01 00:00:00", score=42)]

    html = score_chart(decisions)

    assert str(SignalFilter.BUY_THRESHOLD) in html


def test_score_chart_handles_an_empty_decision_list():

    html = score_chart([])

    assert "No decisions logged yet" in html


def test_score_chart_ignores_entries_without_a_numeric_score():

    decisions = [
        {"timestamp": "2024-01-01 00:00:00", "score": None},
        {"timestamp": "2024-01-01 01:00:00"},
    ]

    html = score_chart(decisions)

    assert "No decisions logged yet" in html


def test_score_chart_renders_when_at_least_one_entry_has_a_score():

    decisions = [
        {"timestamp": "2024-01-01 00:00:00", "score": None},
        _entry("2024-01-01 01:00:00", score=55),
    ]

    html = score_chart(decisions)

    assert "No decisions logged yet" not in html


# ---------------------------------------------------------------------
# Assumption locks / existing-function regression
# ---------------------------------------------------------------------


def test_buy_and_sell_thresholds_are_still_equal():
    """
    score_chart() draws a single reference line under the documented
    assumption that BUY_THRESHOLD == SELL_THRESHOLD. If this ever
    diverges, that assumption silently goes wrong - this test turns it
    into a loud failure instead.
    """

    assert SignalFilter.BUY_THRESHOLD == SignalFilter.SELL_THRESHOLD


def test_existing_signal_distribution_chart_still_handles_empty_input():

    html = signal_distribution_chart([])

    assert "No data" in html
