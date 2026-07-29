import json
from pathlib import Path


class PerformanceDatabase:
    """
    Stores strategy statistics on disk.
    """

    FILE = Path("data/strategy_stats.json")

    @classmethod
    def load(cls):

        if not cls.FILE.exists():
            return {}

        with open(cls.FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def save(cls, stats: dict):

        cls.FILE.parent.mkdir(exist_ok=True)

        with open(cls.FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=4)