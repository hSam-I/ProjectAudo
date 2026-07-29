import pandas as pd

from app.indicators.macd import calculate_macd


def test_macd():

    df = pd.DataFrame(
        {
            "close": list(range(1, 80))
        }
    )

    df = calculate_macd(df)

    assert "macd" in df.columns
    assert "macd_signal" in df.columns
    assert "macd_histogram" in df.columns

    assert not df["macd"].isna().all()