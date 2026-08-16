"""
First test file for the FastAPI app itself (app.web.server) - both
routes rendered through TestClient, with all data sources monkeypatched
so no test here ever touches the network.
"""

import pytest
from fastapi.testclient import TestClient

from app.data.binance_provider import BinanceProvider
from app.data.exceptions import DataProviderError
from app.execution.live_decision_log import LiveDecisionLog
from app.execution.live_state_store import LiveStateStore
from app.execution.live_status_store import LiveStatusStore
from app.web.server import app


@pytest.fixture(autouse=True)
def _isolate_stores(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveStatusStore, "FILE", tmp_path / "live_status.json")
    monkeypatch.setattr(LiveStateStore, "FILE", tmp_path / "live_state.json")
    monkeypatch.setattr(LiveDecisionLog, "FILE", tmp_path / "decisions.jsonl")


@pytest.fixture
def client():
    return TestClient(app)


def test_home_route_returns_200_when_data_provider_fails(client, monkeypatch):
    """
    "/" already falls back to an N/A dict on DataProviderError (see
    load_dashboard_data) - pinned here as this suite's first coverage
    of the route actually being reachable through the FastAPI app.
    """

    def fake_fetch_ohlcv(self, symbol, timeframe, limit):
        raise DataProviderError("simulated outage")

    monkeypatch.setattr(BinanceProvider, "fetch_ohlcv", fake_fetch_ohlcv)

    response = client.get("/")

    assert response.status_code == 200
    assert "PROJECT AUDO" in response.text


def test_live_route_returns_200_when_no_data_exists(client):

    response = client.get("/live")

    assert response.status_code == 200
    assert "No live process has run yet" in response.text


def test_live_route_returns_200_with_status_and_decisions(client):

    from app.core.enums import Signal
    from app.core.time_utils import utc_now
    from app.market.regime import MarketRegime

    LiveStatusStore.save(
        symbol="BTC/USDT",
        mode="observe",
        started_at=str(utc_now()),
        restart_count=0,
        last_poll_at=str(utc_now()),
        next_poll_due_at=str(utc_now()),
        poll_count=1,
        error_count=0,
        last_error=None,
    )

    LiveDecisionLog.append(
        timestamp=str(utc_now()),
        symbol="BTC/USDT",
        raw_signal=Signal.HOLD,
        signal=Signal.HOLD,
        score=10,
        regime=MarketRegime.RANGING,
    )

    response = client.get("/live")

    assert response.status_code == 200
    assert "BTC/USDT" in response.text


def test_live_route_renders_corrupt_state_instead_of_500(client):

    LiveStatusStore.FILE.parent.mkdir(exist_ok=True)
    LiveStatusStore.FILE.write_text("{not valid json", encoding="utf-8")

    response = client.get("/live")

    assert response.status_code == 200
    assert "corrupt" in response.text.lower()


def test_live_page_embeds_all_three_charts(client):

    from app.core.enums import Signal
    from app.core.time_utils import utc_now
    from app.market.regime import MarketRegime

    LiveStatusStore.save(
        symbol="BTC/USDT",
        mode="observe",
        started_at=str(utc_now()),
        restart_count=0,
        last_poll_at=str(utc_now()),
        next_poll_due_at=str(utc_now()),
        poll_count=1,
        error_count=0,
        last_error=None,
    )

    LiveDecisionLog.append(
        timestamp=str(utc_now()),
        symbol="BTC/USDT",
        raw_signal=Signal.BUY,
        signal=Signal.BUY,
        score=70,
        regime=MarketRegime.RANGING,
        candle={"open": 100.0, "high": 105.0, "low": 99.0, "close": 103.0},
    )

    response = client.get("/live")

    assert response.status_code == 200
    assert "Price &amp; Signals" in response.text or "Price & Signals" in response.text
    assert "Decision Score" in response.text
    assert "Signal Distribution" in response.text


def test_live_page_renders_when_decisions_have_no_ohlc(client):
    """
    End-to-end backward-compatibility lock: entries logged before this
    turn added OHLC to LiveDecisionLog lack open/high/low/close entirely
    - the whole page (including the new candlestick chart) must still
    render, not 500.
    """

    from app.core.enums import Signal
    from app.core.time_utils import utc_now
    from app.market.regime import MarketRegime

    LiveStatusStore.save(
        symbol="BTC/USDT",
        mode="observe",
        started_at=str(utc_now()),
        restart_count=0,
        last_poll_at=str(utc_now()),
        next_poll_due_at=str(utc_now()),
        poll_count=1,
        error_count=0,
        last_error=None,
    )

    # No `candle=` given - the exact shape of a pre-upgrade entry.
    LiveDecisionLog.append(
        timestamp=str(utc_now()),
        symbol="BTC/USDT",
        raw_signal=Signal.HOLD,
        signal=Signal.HOLD,
        score=10,
        regime=MarketRegime.RANGING,
    )

    response = client.get("/live")

    assert response.status_code == 200
    assert "No price data logged yet" in response.text
