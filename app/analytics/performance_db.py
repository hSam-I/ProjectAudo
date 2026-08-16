import json
import os

from app.config.paths import DATA_DIR


class PerformanceDatabase:
    """
    Stores strategy statistics on disk.
    """

    FILE = DATA_DIR / "strategy_stats.json"

    @classmethod
    def load(cls):

        if not cls.FILE.exists():
            return {}

        with open(cls.FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def save(cls, stats: dict):
        """
        Writes to a temp file then os.replace()'s it into place, so a
        crash mid-write can never leave a truncated/corrupt JSON file
        for the next load() to choke on. This matters now that
        register_trade() can be called repeatedly from a long-running
        live paper-trading process (via enable_voting), not just from
        short-lived one-shot backtests.
        """

        cls.FILE.parent.mkdir(exist_ok=True)

        temp_path = cls.FILE.with_suffix(".tmp")

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=4)

        os.replace(temp_path, cls.FILE)