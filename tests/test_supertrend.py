import pandas as pd

from app.indicators.supertrend import SuperTrend


def test_supertrend():

    df = pd.DataFrame(
        {
            "high": list(range(2, 202)),
            "low": list(range(0, 200)),
            "close": list(range(1, 201)),
        }
    )

    df = SuperTrend.calculate(df)

    assert "supertrend" in df.columns
    assert "supertrend_direction" in df.columns