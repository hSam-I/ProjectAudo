import pandas as pd

from app.data.validator import DataValidator


def _make_df(n=10, interval_ms=3_600_000):

    timestamps = pd.date_range(
        "2024-01-01",
        periods=n,
        freq=f"{interval_ms}ms",
    )

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": range(n),
            "high": range(n),
            "low": range(n),
            "close": range(n),
            "volume": range(n),
        }
    )


def test_validate_rejects_empty_dataframe():

    assert DataValidator.validate(pd.DataFrame()) is False


def test_validate_rejects_null_values():

    df = _make_df()

    df.loc[3, "close"] = None

    assert DataValidator.validate(df) is False


def test_validate_accepts_clean_evenly_spaced_data():

    df = _make_df()

    assert DataValidator.validate(df) is True


def test_validate_rejects_missing_candle_gap():
    """
    Simulates the exchange skipping a candle: one gap is 2x every
    other gap in the series.
    """

    df = _make_df(n=10)

    df = df.drop(index=5).reset_index(drop=True)

    assert DataValidator.validate(df) is False


def test_validate_accepts_data_without_timestamp_column():
    """
    Gap detection only applies when a timestamp column exists;
    it must not break validation of data that doesn't have one.
    """

    df = pd.DataFrame(
        {
            "open": [1, 2, 3],
            "close": [1, 2, 3],
        }
    )

    assert DataValidator.validate(df) is True
