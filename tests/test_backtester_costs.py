from app.backtesting.backtester import Backtester
from app.config.settings import settings

from tests.test_end_to_end import _build_synthetic_ohlcv


def test_backtester_applies_commission_and_slippage_from_settings(monkeypatch):
    """
    Backtester used to hardcode PaperBroker's own defaults instead of
    forwarding settings.commission / settings.slippage, so changing
    those settings had zero effect on backtest results. This locks
    the wiring in: a much higher configured cost must produce a worse
    realized balance than a zero-cost run on the same trades.
    """

    df = _build_synthetic_ohlcv()

    monkeypatch.setattr(settings, "commission", 0.0)
    monkeypatch.setattr(settings, "slippage", 0.0)

    zero_cost = Backtester().run(df.copy())

    monkeypatch.setattr(settings, "commission", 0.05)
    monkeypatch.setattr(settings, "slippage", 0.02)

    high_cost = Backtester().run(df.copy())

    assert zero_cost.total_trades >= 1
    assert high_cost.total_trades >= 1

    assert high_cost.balance < zero_cost.balance
