"""
Covers app.main.run_funding_arbitrage()/run_funding_arb_status(): wires
FundingArbitrageTrader behind `python -m app.main --funding-arb` and
prints a one-shot on-disk summary behind `--funding-arb-status`.
run_forever() is always monkeypatched (it's an infinite loop) - these
tests verify entrypoint wiring/console formatting, not the loop itself
(covered by tests/test_funding_trader.py).
"""

import pytest

import app.main as main_module
from app.arbitrage.arbitrage_state_store import ArbitrageStateStore
from app.arbitrage.arbitrage_status_store import ArbitrageStatusStore
from app.arbitrage.funding_trader import FundingArbitrageTrader
from app.arbitrage.position import ArbitragePosition
from app.config.settings import settings


@pytest.fixture(autouse=True)
def _isolate_arbitrage_stores(tmp_path, monkeypatch):

    monkeypatch.setattr(
        ArbitrageStateStore, "FILE", tmp_path / "arbitrage_state.json",
    )
    monkeypatch.setattr(
        ArbitrageStatusStore, "FILE", tmp_path / "arbitrage_status.json",
    )


# ----------------------------------------------------------------
# run_funding_arbitrage
# ----------------------------------------------------------------


def test_starts_a_trader_for_the_configured_symbol(monkeypatch):

    monkeypatch.setattr(settings, "funding_arb_symbol", "ETH/USDT")

    calls = {"symbol": None, "started": False}

    def fake_run_forever(self):
        calls["symbol"] = self.symbol
        calls["started"] = True

    monkeypatch.setattr(FundingArbitrageTrader, "run_forever", fake_run_forever)

    main_module.run_funding_arbitrage()

    assert calls["started"] is True
    assert calls["symbol"] == "ETH/USDT"


def test_stops_cleanly_on_keyboard_interrupt(monkeypatch):

    def fake_run_forever(self):
        raise KeyboardInterrupt

    monkeypatch.setattr(FundingArbitrageTrader, "run_forever", fake_run_forever)

    # Must not raise - a Ctrl+C during a long-running loop should exit
    # cleanly, not crash with a traceback.
    main_module.run_funding_arbitrage()


# ----------------------------------------------------------------
# run_funding_arb_status
# ----------------------------------------------------------------


def test_never_run_prints_a_clear_message(capsys):

    main_module.run_funding_arb_status()

    output = capsys.readouterr().out

    assert "No funding-arbitrage process has run yet" in output
    assert "--funding-arb" in output


def test_corrupt_status_file_prints_the_error_instead_of_crashing(capsys):

    ArbitrageStatusStore.FILE.parent.mkdir(exist_ok=True)
    ArbitrageStatusStore.FILE.write_text("{not valid json", encoding="utf-8")

    main_module.run_funding_arb_status()

    output = capsys.readouterr().out

    assert "corrupt" in output.lower()


def _save_heartbeat(**overrides):

    defaults = dict(
        symbol="BTC/USDT",
        started_at="2026-01-01T00:00:00",
        restart_count=0,
        last_poll_at="2026-01-01T08:00:00",
        next_poll_due_at="2026-01-01T16:00:00",
        poll_count=3,
        error_count=0,
        last_error=None,
        position_status=None,
        margin_ratio=None,
        cumulative_funding=None,
    )

    defaults.update(overrides)

    ArbitrageStatusStore.save(**defaults)


def test_no_open_position_prints_a_placeholder(capsys):

    _save_heartbeat()

    main_module.run_funding_arb_status()

    output = capsys.readouterr().out

    assert "BTC/USDT" in output
    assert "No open position" in output


def test_open_position_prints_margin_ratio_and_cumulative_funding(capsys):

    _save_heartbeat(
        position_status="OPEN",
        margin_ratio=0.1234,
        cumulative_funding=42.5,
    )

    main_module.run_funding_arb_status()

    output = capsys.readouterr().out

    assert "Position Status  : OPEN" in output
    assert "0.1234" in output
    assert "+42.5000" in output


def test_closed_positions_are_summarized(capsys):

    _save_heartbeat()

    closed = ArbitragePosition(
        symbol="BTC/USDT",
        leverage=1,
        maintenance_margin_rate=0.004,
        entry_time="t1",
        spot_entry_price=60000.0,
        spot_qty=0.1,
        perp_entry_price=60000.0,
        perp_qty=0.1,
        margin=6000.0,
        status="CLOSED",
        cumulative_funding=15.0,
    )

    ArbitrageStateStore.save(None, [closed])

    main_module.run_funding_arb_status()

    output = capsys.readouterr().out

    assert "Closed Positions : 1" in output
    assert "+15.0000" in output


def test_no_closed_positions_shows_zero(capsys):

    _save_heartbeat()

    main_module.run_funding_arb_status()

    output = capsys.readouterr().out

    assert "Closed Positions : 0" in output


def test_corrupt_state_file_prints_the_error(capsys):

    _save_heartbeat()

    ArbitrageStateStore.FILE.parent.mkdir(exist_ok=True)
    ArbitrageStateStore.FILE.write_text("{not valid json", encoding="utf-8")

    main_module.run_funding_arb_status()

    output = capsys.readouterr().out

    assert "State file is corrupt" in output
