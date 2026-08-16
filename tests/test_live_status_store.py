"""
Covers app.execution.live_status_store.LiveStatusStore - the heartbeat
the live loop writes on every poll, read by the --live-status CLI/--web
hub to show whether the process is still alive.
"""

import os

import pytest

from app.execution.live_state_store import LiveStateCorruptError
from app.execution.live_status_store import LiveStatusStore


def _save(**overrides):

    kwargs = {
        "symbol": "BTC/USDT",
        "mode": "observe",
        "started_at": "2024-01-01 00:00:00",
        "restart_count": 0,
        "last_poll_at": "2024-01-01 01:00:00",
        "next_poll_due_at": "2024-01-01 02:00:00",
        "poll_count": 1,
        "error_count": 0,
        "last_error": None,
    }

    kwargs.update(overrides)

    LiveStatusStore.save(**kwargs)


def test_load_returns_none_when_no_file_exists(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveStatusStore, "FILE", tmp_path / "live_status.json")

    assert LiveStatusStore.load() is None


def test_save_and_load_roundtrip(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveStatusStore, "FILE", tmp_path / "live_status.json")

    _save(poll_count=5, error_count=2, last_error="boom", restart_count=3)

    saved = LiveStatusStore.load()

    assert saved["symbol"] == "BTC/USDT"
    assert saved["mode"] == "observe"
    assert saved["poll_count"] == 5
    assert saved["error_count"] == 2
    assert saved["last_error"] == "boom"
    assert saved["restart_count"] == 3
    assert saved["pid"] == os.getpid()


def test_save_records_none_last_poll_and_last_error_when_never_polled(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveStatusStore, "FILE", tmp_path / "live_status.json")

    _save(last_poll_at=None, poll_count=0, last_error=None)

    saved = LiveStatusStore.load()

    assert saved["last_poll_at"] is None
    assert saved["last_error"] is None


def test_load_raises_on_corrupt_json(tmp_path, monkeypatch):

    file = tmp_path / "live_status.json"
    file.write_text("{not valid json", encoding="utf-8")

    monkeypatch.setattr(LiveStatusStore, "FILE", file)

    with pytest.raises(LiveStateCorruptError):
        LiveStatusStore.load()


def test_save_uses_atomic_write(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveStatusStore, "FILE", tmp_path / "live_status.json")

    calls = {"count": 0}

    original_replace = os.replace

    def counting_replace(src, dst):
        calls["count"] += 1
        return original_replace(src, dst)

    monkeypatch.setattr(os, "replace", counting_replace)

    _save()

    assert calls["count"] == 1
    assert not (tmp_path / "live_status.tmp").exists()


def test_no_secret_or_real_order_keywords_in_source():
    """
    Regression for the plan's Bulgu 1: this new store's docstrings must
    never contain the literal substring "secret" (the existing
    live_*.py security glob test in test_live_trader.py checks the
    whole app/execution/live_*.py family for it, so this is a narrower,
    file-local pin of the same constraint for fast local feedback).
    """

    from pathlib import Path

    source = Path(__file__).resolve().parent.parent / "app" / "execution" / "live_status_store.py"

    assert "secret" not in source.read_text(encoding="utf-8")
