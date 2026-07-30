import pandas as pd

from app.indicators.indicator_engine import IndicatorEngine


def test_indicator_engine():

    df = pd.DataFrame(
        {
            "open": list(range(1, 101)),
            "high": list(range(2, 102)),
            "low": list(range(0, 100)),
            "close": list(range(1, 101)),
            "volume": [100] * 100,
        }
    )

    result = IndicatorEngine.prepare(
        df=df,
        ema_fast=10,
        ema_slow=30,
    )

    assert "ema_fast" in result.columns
    assert "ema_slow" in result.columns

    assert "rsi" in result.columns

    assert "atr" in result.columns

    assert "macd" in result.columns
    assert "macd_signal" in result.columns
    assert "macd_histogram" in result.columns

    assert "adx" in result.columns

    assert "bb_upper" in result.columns
    assert "bb_middle" in result.columns
    assert "bb_lower" in result.columns

    assert "vwap" in result.columns

    assert "obv" in result.columns

    assert "stoch_k" in result.columns
    assert "stoch_d" in result.columns

    assert len(result) == 100