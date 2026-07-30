import pandas as pd

from app.features.feature_pipeline import (
    FeaturePipeline,
)


def test_feature_pipeline():

    df = pd.DataFrame(
        {
            "open": list(range(1, 150)),
            "high": list(range(2, 151)),
            "low": list(range(0, 149)),
            "close": list(range(1, 150)),
            "volume": [100] * 149,
        }
    )

    result = FeaturePipeline.build(df)

    assert "ema_fast" in result.columns
    assert "ema_slow" in result.columns