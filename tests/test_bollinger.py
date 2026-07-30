import pandas as pd

from app.indicators.bollinger import (
    BollingerBands,
)


def test_bollinger():

    df = pd.DataFrame(
        {
            "close": list(range(1, 201)),
        }
    )

    df = BollingerBands.calculate(df)

    assert "bb_upper" in df.columns
    assert "bb_middle" in df.columns
    assert "bb_lower" in df.columns

    assert not df["bb_upper"].isna().all()