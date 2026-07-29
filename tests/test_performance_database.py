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