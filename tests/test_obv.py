import pandas as pd

from app.indicators.obv import OBV


def test_obv():

    df = pd.DataFrame(
        {
            "close": [10, 11, 12, 11, 13, 12],
            "volume": [100, 120, 150, 80, 200, 90],
        }
    )

    df = OBV.calculate(df)

    assert "obv" in df.columns

    assert len(df["obv"]) == len(df)

    assert not df["obv"].isna().any()