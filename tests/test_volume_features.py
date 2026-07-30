import pandas as pd

from app.features.volume_features import (
    VolumeFeatures,
)


def test_volume_features():

    df = pd.DataFrame(
        {
            "close": [100] * 30,
            "volume": [100] * 29 + [300],
            "vwap": [99] * 30,
            "obv": list(range(30)),
        }
    )

    df = VolumeFeatures.build(df)

    assert "avg_volume" in df.columns
    assert "relative_volume" in df.columns

    assert "volume_spike" in df.columns

    assert "above_vwap" in df.columns
    assert "vwap_distance" in df.columns

    assert "obv_change" in df.columns
    assert "obv_up" in df.columns
    assert "obv_down" in df.columns