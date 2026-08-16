"""
Covers app.web.live_status_data.load_live_status() - the read-only
layer behind both the /live web route and the --live-status CLI. It
must never touch the network (unlike load_dashboard_data(), which
fetches fresh market data) and must degrade to a clear display state
instead of crashing on a never-run, corrupt, or mid-write file.
"""

import pandas as pd
import pytest

from app.core.time_utils import utc_now
from app.data.binance_provider import BinanceProvider
from app.execution.live_decision_log import LiveDecisionLog
from app.execution.live_state_store import LiveStateStore
from app.execution.live_status_store import LiveStatusStore
from app.web.live_status_data import load_live_status


@pytest.fixture(autouse=True)
def _isolate_stores(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveStatusStore, "FILE", tmp_path / "live_status.json")
    monkeypatch.setattr(LiveStateStore, "FILE", tmp_path / "live_state.json")
    monkeypatch.setattr(LiveDecisionLog, "FILE", tmp_path / "decisions.jsonl")


@pytest.fixture(autouse=True)
def _forbid_network_calls(monkeypatch):

    def _fail(*args, **kwargs):
        raise AssertionError("load_live_status() must never touch the network")

    monkeypatch.setattr(BinanceProvider, "fetch_ohlcv", _fail)
    monkeypatch.setattr(BinanceProvider, "fetch_ticker", _fail)


def _save_status(**overrides):

    kwargs = {
        "symbol": "BTC/USDT",
        "mode": "observe",
        "started_at": "2024-01-01 00:00:00",
        "restart_count": 0,
        "last_poll_at": "2024-01-01 01:00:00",
        "next_poll_due_at": str(utc_now() + pd.Timedelta(hours=1)),
        "poll_count": 3,
        "error_count": 0,
        "last_error": None,
    }

    kwargs.update(overrides)

    LiveStatusStore.save(**kwargs)


def test_never_run_reports_has_run_false():

    result = load_live_status()

    assert result["has_run"] is False
    assert result["corrupt"] is False
    assert result["health"] == "NO DATA"
    assert result["decisions"] == []


def test_corrupt_status_file_reports_corrupt_state():

    LiveStatusStore.FILE.parent.mkdir(exist_ok=True)
    LiveStatusStore.FILE.write_text("{not valid json", encoding="utf-8")

    result = load_live_status()

    assert result["has_run"] is True
    assert result["corrupt"] is True
    assert result["corrupt_error"] is not None


def test_corrupt_paper_state_file_reports_corrupt_state():

    _save_status(mode="paper")

    LiveStateStore.FILE.parent.mkdir(exist_ok=True)
    LiveStateStore.FILE.write_text("{not valid json", encoding="utf-8")

    result = load_live_status()

    assert result["corrupt"] is True


def test_observe_mode_healthy_when_next_poll_is_in_the_future():

    _save_status(mode="observe")

    result = load_live_status()

    assert result["has_run"] is True
    assert result["mode"] == "observe"
    assert result["paper_trading"] is False
    assert result["health"] == "OK"
    assert result["overdue_by_seconds"] is None


def test_health_is_overdue_when_next_poll_is_in_the_past():

    _save_status(
        next_poll_due_at=str(utc_now() - pd.Timedelta(minutes=5)),
    )

    result = load_live_status()

    assert result["health"] == "OVERDUE"
    assert result["overdue_by_seconds"] > 0


def test_health_is_no_data_when_next_poll_due_at_missing():

    _save_status(next_poll_due_at=None)

    result = load_live_status()

    assert result["health"] == "NO DATA"


def test_paper_mode_reports_balance_and_open_position_count():

    _save_status(mode="paper")

    portfolio_state = {
        "initial_balance": 10000,
        "balance": 10450.0,
        "balance_history": [10000, 10450.0],
        "trades": [
            {
                "symbol": "BTC/USDT",
                "side": "BUY",
                "entry_price": 100.0,
                "quantity": 1.0,
                "entry_time": "2024-01-01 00:00:00",
                "stop_loss": 95.0,
                "take_profit": 110.0,
                "risk_amount": 50.0,
                "status": "OPEN",
                "exit_price": None,
                "exit_time": None,
                "profit": 0.0,
            },
        ],
        "last_processed_timestamp": "2024-01-01 05:00:00",
    }

    import json

    LiveStateStore.FILE.parent.mkdir(exist_ok=True)

    with open(LiveStateStore.FILE, "w", encoding="utf-8") as f:
        json.dump(portfolio_state, f)

    result = load_live_status()

    assert result["paper_trading"] is True
    assert result["balance"] == 10450.0
    assert result["open_position_count"] == 1


def test_observe_mode_never_reports_balance():

    _save_status(mode="observe")

    result = load_live_status()

    assert result["paper_trading"] is False
    assert result["balance"] is None
    assert result["open_position_count"] is None


def test_decisions_are_read_from_the_decision_log():

    _save_status(mode="observe")

    from app.core.enums import Signal
    from app.market.regime import MarketRegime

    LiveDecisionLog.append(
        timestamp="2024-01-01 01:00:00",
        symbol="BTC/USDT",
        raw_signal=Signal.BUY,
        signal=Signal.BUY,
        score=70,
        regime=MarketRegime.RANGING,
    )

    result = load_live_status()

    assert len(result["decisions"]) == 1
    assert result["decisions"][0]["symbol"] == "BTC/USDT"
