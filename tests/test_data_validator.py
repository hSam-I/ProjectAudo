import pandas as pd

from app.data.validator import DataValidator


def _valid_df(n: int = 60) -> pd.DataFrame:

    rows = []

    price = 100.0

    for i in range(n):

        rows.append(
            {
                "timestamp": pd.Timestamp("2024-01-01") + pd.Timedelta(hours=i),
                "open": price,
                "high": price + 1,
                "low": price - 1,
                "close": price + 0.5,
                "volume": 1000,
            }
        )

        price += 0.1

    return pd.DataFrame(rows)


def test_validate_accepts_well_formed_data():

    assert DataValidator.validate(_valid_df()) is True


def test_validate_rejects_empty_dataframe():

    assert DataValidator.validate(pd.DataFrame()) is False


def test_validate_rejects_missing_columns():

    df = _valid_df().drop(columns=["volume"])

    assert DataValidator.validate(df) is False


def test_validate_rejects_nan_values():

    df = _valid_df()

    df.loc[5, "close"] = float("nan")

    assert DataValidator.validate(df) is False


def test_validate_rejects_too_few_rows():

    df = _valid_df(n=DataValidator.MINIMUM_ROWS - 1)

    assert DataValidator.validate(df) is False


def test_validate_rejects_non_positive_prices():

    df = _valid_df()

    df.loc[0, "open"] = 0

    assert DataValidator.validate(df) is False


def test_validate_rejects_negative_volume():

    df = _valid_df()

    df.loc[0, "volume"] = -1

    assert DataValidator.validate(df) is False


def test_validate_rejects_high_below_open_close():

    df = _valid_df()

    df.loc[3, "high"] = df.loc[3, "close"] - 10

    assert DataValidator.validate(df) is False


def test_validate_rejects_low_above_open_close():

    df = _valid_df()

    df.loc[3, "low"] = df.loc[3, "close"] + 10

    assert DataValidator.validate(df) is False


def test_validate_rejects_duplicate_timestamps():

    df = _valid_df()

    df.loc[10, "timestamp"] = df.loc[9, "timestamp"]

    assert DataValidator.validate(df) is False


def test_validate_rejects_missing_candle_gap():

    df = _valid_df()

    # Blow a 10-hour hole in an otherwise 1-hour-spaced series.
    df.loc[30:, "timestamp"] = (
        df.loc[30:, "timestamp"] + pd.Timedelta(hours=10)
    )

    assert DataValidator.validate(df) is False
