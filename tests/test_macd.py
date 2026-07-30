import pandas as pd

from app.indicators.macd import MACD


def test_macd():

    df = pd.DataFrame(
        {
            "close": list(range(1, 80))
        }
    )

    df = MACD.calculate(df)

    assert "macd" in df.columns
    assert "macd_signal" in df.columns
    assert "macd_histogram" in df.columns

    assert not df["macd"].isna().all()