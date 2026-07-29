from app.analytics.performance_db import PerformanceDatabase


class LearningEngine:
    """
    Updates strategy performance after each trade.
    """

    @staticmethod
    def register_trade(
        strategy_name: str,
        profit: float,
    ):

        db = PerformanceDatabase.load()

        if strategy_name not in db:
            db[strategy_name] = {
                "wins": 0,
                "losses": 0,
            }

        if profit > 0:
            db[strategy_name]["wins"] += 1
        else:
            db[strategy_name]["losses"] += 1

        PerformanceDatabase.save(db)