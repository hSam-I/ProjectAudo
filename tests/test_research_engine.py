import pandas as pd

from app.research.research_engine import ResearchEngine


def test_research_engine():

    df = pd.DataFrame(
        {
            "close": [100, 101, 102],
            "atr": [2, 2, 2],
        }
    )

    profits = [
        100,
        -50,
        75,
        30,
    ]

    engine = ResearchEngine()

    report = engine.run(
        profits,
        df,
    )

    assert "risk_of_ruin" in report
    assert "average_result" in report
    assert "best_result" in report
    assert "worst_result" in report
    assert report["scenario_count"] == 5