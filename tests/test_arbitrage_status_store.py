import pytest

from app.arbitrage.arbitrage_state_store import ArbitrageStateCorruptError
from app.arbitrage.arbitrage_status_store import ArbitrageStatusStore


@pytest.fixture(autouse=True)
def _isolate_status_store(tmp_path, monkeypatch):

    monkeypatch.setattr(
        ArbitrageStatusStore, "FILE", tmp_path / "arbitrage_status.json",
    )


def _save(**overrides):

    defaults = dict(
        symbol="BTC/USDT",
        started_at="2026-01-01T00:00:00",
        restart_count=0,
        last_poll_at=None,
        next_poll_due_at="2026-01-01T08:00:00",
        poll_count=0,
        error_count=0,
        last_error=None,
        position_status=None,
        margin_ratio=None,
        cumulative_funding=None,
    )

    defaults.update(overrides)

    ArbitrageStatusStore.save(**defaults)


def test_load_returns_none_when_no_file_exists():

    assert ArbitrageStatusStore.load() is None


def test_save_then_load_round_trips_fields():

    _save(
        poll_count=5,
        error_count=1,
        last_error="boom",
        position_status="OPEN",
        margin_ratio=0.12,
        cumulative_funding=42.5,
    )

    state = ArbitrageStatusStore.load()

    assert state["symbol"] == "BTC/USDT"
    assert state["poll_count"] == 5
    assert state["error_count"] == 1
    assert state["last_error"] == "boom"
    assert state["position_status"] == "OPEN"
    assert state["margin_ratio"] == pytest.approx(0.12)
    assert state["cumulative_funding"] == pytest.approx(42.5)
    assert "pid" in state
    assert state["version"] == 1


def test_no_open_position_fields_are_null():

    _save()

    state = ArbitrageStatusStore.load()

    assert state["position_status"] is None
    assert state["margin_ratio"] is None
    assert state["cumulative_funding"] is None


def test_save_is_atomic_no_temp_file_left_behind():

    _save()

    temp_path = ArbitrageStatusStore.FILE.with_suffix(".tmp")

    assert ArbitrageStatusStore.FILE.exists()
    assert not temp_path.exists()


def test_load_raises_on_corrupt_json():

    ArbitrageStatusStore.FILE.parent.mkdir(exist_ok=True)
    ArbitrageStatusStore.FILE.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ArbitrageStateCorruptError):
        ArbitrageStatusStore.load()
