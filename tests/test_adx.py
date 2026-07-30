import pandas as pd

from app.indicators.adx import ADX


def test_adx():

    df = pd.DataFrame(
        {
            "high": list(range(2, 202)),
            "low": list(range(1, 201)),
            "close": list(range(1, 201)),
        }
    )

    df = ADX.calculate(df)

    assert "adx" in df.columns

    assert not df["adx"].isna().all()