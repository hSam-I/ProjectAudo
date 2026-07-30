import pandas as pd

from app.optimization.scenario_runner import ScenarioRunner


def test_runner():

    df = pd.DataFrame(
        {
            "close": [100],
            "atr": [2],
        }
    )

    runner = ScenarioRunner()

    scenarios = runner.run(df)

    assert len(scenarios) == 5

    assert "normal" in scenarios
    assert "flash_crash" in scenarios
    assert "bull_market" in scenarios
    assert "high_volatility" in scenarios
    assert "gap_down" in scenarios


def test_scenario_names():

    runner = ScenarioRunner()

    names = runner.scenario_names()

    assert len(names) == 5
    assert "normal" in names
    assert "flash_crash" in names