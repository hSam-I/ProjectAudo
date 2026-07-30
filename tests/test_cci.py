import pandas as pd

from app.indicators.cci import CCI


def test_cci():

    df = pd.DataFrame(
        {
            "high": list(range(2, 202)),
            "low": list(range(0, 200)),
            "close": list(range(1, 201)),
        }
    )

    df = CCI.calculate(df)

    assert "cci" in df.columns

    assert not df["cci"].isna().all()