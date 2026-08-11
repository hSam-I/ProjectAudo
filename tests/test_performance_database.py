import os
from pathlib import Path

from app.analytics.performance_db import PerformanceDatabase


def test_database_save_load(tmp_path):

    db_file = tmp_path / "stats.json"

    PerformanceDatabase.FILE = db_file

    data = {
        "ema_rsi": {
            "wins": 12,
            "losses": 4,
        }
    }

    PerformanceDatabase.save(data)

    loaded = PerformanceDatabase.load()

    assert loaded == data


def test_save_uses_atomic_write(tmp_path, monkeypatch):
    """
    Regression test for the live-paper-trading turn: save() must write
    to a temp file and os.replace() it into place, not truncate the
    real file directly - a crash mid-write must never leave a
    corrupt/truncated data/strategy_stats.json for load() to choke on.
    This matters now that a long-running live process (with
    enable_voting=True) calls save() repeatedly, not just short-lived
    one-shot backtests.
    """

    PerformanceDatabase.FILE = tmp_path / "stats.json"

    calls = {"count": 0}

    original_replace = os.replace

    def counting_replace(src, dst):
        calls["count"] += 1
        return original_replace(src, dst)

    monkeypatch.setattr(os, "replace", counting_replace)

    PerformanceDatabase.save({"ema_rsi": {"wins": 1, "losses": 0}})

    assert calls["count"] == 1
    assert PerformanceDatabase.load() == {"ema_rsi": {"wins": 1, "losses": 0}}
    assert not (tmp_path / "stats.tmp").exists()