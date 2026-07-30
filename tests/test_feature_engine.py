import pandas as pd

from app.features.feature_engine import FeatureEngine


def test_feature_engine():

    df = pd.DataFrame(
        {
            "open": [100] * 40,
            "high": [102] * 40,
            "low": [98] * 40,
            "close": [101] * 40,
            "volume": [1000] * 40,

            "ema_fast": [102] * 40,
            "ema_slow": [100] * 40,

            "adx": [30] * 40,
            "atr": [2] * 40,
            "atr_percent": [2] * 40,

            "bb_upper": [103] * 40,
            "bb_middle": [101] * 40,
            "bb_lower": [99] * 40,

            "vwap": [100] * 40,
            "obv": list(range(40)),

            "rsi": [60] * 40,

            "macd": [1] * 40,
            "macd_signal": [0.5] * 40,
            "macd_histogram": [0.5] * 40,

            "senkou_span_a": [99] * 40,
            "senkou_span_b": [98] * 40,
        }
    )

    df = FeatureEngine.build(df)

    assert "trend_strength" in df.columns
    assert "macd_positive" in df.columns
    assert "volume_spike" in df.columns
    assert "hammer" in df.columns
    assert "trend_market" in df.columns