"""
Covers app.main.run_live_paper_trading() (Phase 1): wires
app.execution.live_trader.LiveTrader behind `python -m app.main --live`.
LiveTrader.run_forever() is an infinite loop, so it is always
monkeypatched here - these tests only verify the entrypoint's wiring
and its KeyboardInterrupt handling, not the loop itself (covered by
test_live_trader.py/test_live_feed.py).
"""

from app.config.settings import settings
from app.execution.live_trader import LiveTrader


def test_run_live_paper_trading_starts_a_trader_for_the_first_symbol(monkeypatch):

    monkeypatch.setattr(settings, "symbols", ["BTC/USDT", "ETH/USDT"])

    calls = {"symbol": None, "started": False}

    def fake_run_forever(self):
        calls["symbol"] = self.symbol
        calls["started"] = True

    monkeypatch.setattr(LiveTrader, "run_forever", fake_run_forever)

    from app.main import run_live_paper_trading

    run_live_paper_trading()

    assert calls["started"] is True
    assert calls["symbol"] == "BTC/USDT"


def test_run_live_paper_trading_stops_cleanly_on_keyboard_interrupt(monkeypatch, capsys):

    monkeypatch.setattr(settings, "symbols", ["BTC/USDT"])

    def fake_run_forever(self):
        raise KeyboardInterrupt

    monkeypatch.setattr(LiveTrader, "run_forever", fake_run_forever)

    from app.main import run_live_paper_trading

    # Must not raise - a Ctrl+C during a long-running live loop should
    # exit cleanly, not crash with a traceback.
    run_live_paper_trading()
