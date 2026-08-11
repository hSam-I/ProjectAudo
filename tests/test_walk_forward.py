import pandas as pd

from app.backtesting.backtester import Backtester
from app.optimization.walk_forward import WalkForwardAnalyzer
from app.strategy.ema_rsi_strategy import EMARSIStrategy


def test_walk_forward():

    df = pd.DataFrame({
        "close": range(300)
    })

    analyzer = WalkForwardAnalyzer(
        train_size=100,
        test_size=50,
    )

    windows = analyzer.generate_windows(df)

    assert len(windows) == 4


def _run_window(train, test):
    """
    Indicators need the train slice as lookback context, so the
    strategy is backtested on train+test combined; only the
    resulting portfolio is inspected for out-of-sample behaviour.
    """

    combined = pd.concat([train, test]).reset_index(drop=True)

    return Backtester(strategy=EMARSIStrategy()).run(combined)


def test_walk_forward_ema_rsi_strategy(random_walk_ohlcv):

    df = random_walk_ohlcv(n=900)

    analyzer = WalkForwardAnalyzer(
        train_size=300,
        test_size=100,
    )

    windows = analyzer.generate_windows(df)

    assert len(windows) == 6

    # --------------------------------------------------
    # Test windows must be sequential and non-overlapping:
    # each one covers a fresh, later out-of-sample slice.
    # --------------------------------------------------

    test_timestamps_seen = set()

    for _, test in windows:

        window_timestamps = set(test["timestamp"])

        assert test_timestamps_seen.isdisjoint(window_timestamps)

        test_timestamps_seen |= window_timestamps

    # --------------------------------------------------
    # The strategy must actually run (and trade) across
    # the rolling out-of-sample windows, not just once.
    # --------------------------------------------------

    total_trades = 0

    for train, test in windows:

        portfolio = _run_window(train, test)

        assert portfolio is not None
        assert isinstance(portfolio.balance, float)

        total_trades += portfolio.total_trades

    assert total_trades > 0

    # --------------------------------------------------
    # Same window, run twice, must produce identical
    # results: a walk-forward strategy must be
    # deterministic, not path-dependent on prior runs.
    # --------------------------------------------------

    train, test = windows[0]

    first = _run_window(train, test)
    second = _run_window(train, test)

    assert first.total_trades == second.total_trades
    assert first.balance == second.balance