"""
Covers app.main's optional research step (Step 2 of the orphan-module
integration): when settings.enable_research is True, main() runs
ResearchEngine + ResearchReportBuilder after the backtest and writes
reports/research_report.json. Default (False) must leave main()'s
behavior byte-for-byte unchanged from before this step existed.
"""

import json

import pytest

from app.config.settings import settings
from app.data.binance_provider import BinanceProvider


@pytest.fixture
def fake_binance(random_walk_ohlcv, monkeypatch):

    data = random_walk_ohlcv()

    def fake_fetch_ohlcv(self, symbol, timeframe, limit=500):
        return data.copy()

    monkeypatch.setattr(
        BinanceProvider,
        "fetch_ohlcv",
        fake_fetch_ohlcv,
    )

    return data


def test_main_skips_research_report_by_default(fake_binance, monkeypatch, tmp_path):

    monkeypatch.chdir(tmp_path)

    from app.main import main

    main()

    assert not (tmp_path / "reports" / "research_report.json").exists()


def test_main_writes_research_report_when_enabled(fake_binance, monkeypatch, tmp_path):

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "enable_research", True)

    from app.main import main

    main()

    report_path = tmp_path / "reports" / "research_report.json"

    assert report_path.exists()

    report = json.loads(report_path.read_text())

    assert "generated_at" in report
    assert "summary" in report
    assert "risk_of_ruin" in report["summary"]
    assert "survival_probability" in report["summary"]
    assert "scenarios" in report
    assert report["scenarios"]["count"] == 5
    assert "simulation_count" in report


def test_main_writes_research_report_with_no_closed_trades(monkeypatch, tmp_path):
    """
    ResearchEngine.run() must not crash when the backtest closed zero
    trades (MonteCarloSimulator.simulate([]) -> [], RiskOfRuinAnalyzer([])
    -> 0.0) - a flat/no-signal market shouldn't break the research step.
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "enable_research", True)

    import pandas as pd

    def empty_signal_fetch(self, symbol, timeframe, limit=500):

        n = 200

        return pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=n, freq="1h"),
                "open": [100.0] * n,
                "high": [100.5] * n,
                "low": [99.5] * n,
                "close": [100.0] * n,
                "volume": [1000.0] * n,
            }
        )

    monkeypatch.setattr(
        BinanceProvider,
        "fetch_ohlcv",
        empty_signal_fetch,
    )

    from app.main import main

    main()

    report_path = tmp_path / "reports" / "research_report.json"

    assert report_path.exists()

    report = json.loads(report_path.read_text())

    assert report["simulation_count"] == 0
