import pandas as pd

from app.indicators.ichimoku import Ichimoku


def test_ichimoku():

    df = pd.DataFrame(
        {
            "high": list(range(2, 302)),
            "low": list(range(0, 300)),
            "close": list(range(1, 301)),
        }
    )

    df = Ichimoku.calculate(df)

    assert "tenkan_sen" in df.columns
    assert "kijun_sen" in df.columns
    assert "senkou_span_a" in df.columns
    assert "senkou_span_b" in df.columns
    assert "chikou_span" in df.columns