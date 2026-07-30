import pandas as pd

from app.indicators.stochastic import (
    Stochastic,
)


def test_stochastic():

    df = pd.DataFrame(
        {
            "high": list(range(2, 202)),
            "low": list(range(0, 200)),
            "close": list(range(1, 201)),
        }
    )

    df = Stochastic.calculate(df)

    assert "stoch_k" in df.columns
    assert "stoch_d" in df.columns

    assert not df["stoch_k"].isna().all()