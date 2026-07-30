import pandas as pd

from app.indicators.vwap import VWAP


def test_vwap():

    df = pd.DataFrame(
        {
            "high": list(range(2, 202)),
            "low": list(range(0, 200)),
            "close": list(range(1, 201)),
            "volume": [1000] * 200,
        }
    )

    df = VWAP.calculate(df)

    assert "vwap" in df.columns

    assert not df["vwap"].isna().all()