import pytest

from app.arbitrage.arbitrage_state_store import (
    ArbitrageStateCorruptError,
    ArbitrageStateStore,
)
from app.arbitrage.position import ArbitragePosition


@pytest.fixture(autouse=True)
def _isolate_state_store(tmp_path, monkeypatch):

    monkeypatch.setattr(
        ArbitrageStateStore, "FILE", tmp_path / "arbitrage_state.json",
    )


def _position(status="OPEN"):

    return ArbitragePosition(
        symbol="BTC/USDT",
        leverage=3,
        maintenance_margin_rate=0.004,
        entry_time="2026-01-01T00:00:00",
        spot_entry_price=60000.0,
        spot_qty=0.5,
        perp_entry_price=60010.0,
        perp_qty=0.5,
        margin=10000.0,
        status=status,
        cumulative_funding=12.34,
        funding_events=[
            {
                "timestamp": "2026-01-01T08:00:00",
                "funding_rate": 0.0001,
                "mark_price": 60005.0,
                "payment": 3.0,
            },
        ],
    )


def test_load_returns_none_when_no_file_exists():

    assert ArbitrageStateStore.load() is None


def test_restore_returns_none_and_empty_list_when_no_file_exists():

    position, closed = ArbitrageStateStore.restore()

    assert position is None
    assert closed == []


def test_save_then_restore_round_trips_an_open_position():

    original = _position()

    ArbitrageStateStore.save(original, [])

    position, closed = ArbitrageStateStore.restore()

    assert position is not None
    assert position.symbol == "BTC/USDT"
    assert position.status == "OPEN"
    assert position.cumulative_funding == pytest.approx(12.34)
    assert position.funding_events == original.funding_events
    assert closed == []


def test_save_then_restore_round_trips_no_open_position_plus_history():

    closed_one = _position(status="CLOSED")

    ArbitrageStateStore.save(None, [closed_one])

    position, closed = ArbitrageStateStore.restore()

    assert position is None
    assert len(closed) == 1
    assert closed[0].status == "CLOSED"
    assert closed[0].cumulative_funding == pytest.approx(12.34)


def test_save_is_atomic_no_temp_file_left_behind():

    ArbitrageStateStore.save(_position(), [])

    temp_path = ArbitrageStateStore.FILE.with_suffix(".tmp")

    assert ArbitrageStateStore.FILE.exists()
    assert not temp_path.exists()


def test_load_raises_on_corrupt_json():

    ArbitrageStateStore.FILE.parent.mkdir(exist_ok=True)
    ArbitrageStateStore.FILE.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ArbitrageStateCorruptError):
        ArbitrageStateStore.load()


def test_restore_raises_on_corrupt_json_rather_than_resetting():
    """
    Unlike ArbitrageStatusStore, a corrupt arbitrage_state.json must
    never be silently treated as "no state" - it carries real
    funding-collection history.
    """

    ArbitrageStateStore.FILE.parent.mkdir(exist_ok=True)
    ArbitrageStateStore.FILE.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ArbitrageStateCorruptError):
        ArbitrageStateStore.restore()
