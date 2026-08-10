import numpy as np
import pandas as pd

from app.backtesting.backtester import Backtester
from app.backtesting.performance import PerformanceAnalyzer
from app.optimization.walk_forward import WalkForwardAnalyzer
from app.strategy.registry import get_strategy


# Regime name, drift/bar, volatility/bar, length in bars.
_REGIMES = [
    ("uptrend", 0.15, 0.30, 130),
    ("chop", 0.00, 0.45, 110),
    ("downtrend", -0.15, 0.30, 130),
    ("chop_high_vol", 0.00, 0.90, 110),
    ("uptrend_strong", 0.30, 0.40, 120),
    ("downtrend_strong", -0.30, 0.40, 120),
    ("chop", 0.00, 0.45, 110),
    ("uptrend", 0.15, 0.30, 130),
]


def _build_multi_regime_ohlcv(seed: int = 123) -> pd.DataFrame:
    """
    Deterministic OHLCV series spanning 8 distinct ~110-130 bar regimes
    (uptrend / chop / downtrend / high-vol chop / strong moves), so a
    walk-forward split actually sees different market conditions per
    window instead of the one favorable, hand-picked period a single
    fixed backtest would use.
    """

    rng = np.random.default_rng(seed)

    price = 100.0
    closes = []

    for _, drift, vol, length in _REGIMES:

        for _ in range(length):

            price += drift + rng.normal(0, vol)
            price = max(price, 1.0)

            closes.append(price)

    closes = np.array(closes)
    n = len(closes)

    open_ = np.empty(n)
    open_[0] = closes[0]
    open_[1:] = closes[:-1]

    wick = rng.uniform(0.1, 0.4, n)

    high = np.maximum(open_, closes) + wick
    low = np.minimum(open_, closes) - wick
    volume = rng.uniform(500, 1500, n)

    return pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2024-01-01",
                periods=n,
                freq="1h",
            ),
            "open": open_,
            "high": high,
            "low": low,
            "close": closes,
            "volume": volume,
        }
    )


def _run_window(df: pd.DataFrame) -> dict:

    strategy = get_strategy("ema_rsi")

    portfolio = Backtester(
        strategy=strategy,
    ).run(
        df.reset_index(drop=True)
    )

    performance = PerformanceAnalyzer(portfolio)

    return {
        "portfolio": portfolio,
        "trades": portfolio.total_trades,
        "closed": portfolio.closed_trades_count,
        "win_rate": performance.win_rate(),
        "profit_factor": performance.profit_factor(),
        "max_drawdown": performance.max_drawdown(),
        "return_pct": (
            (portfolio.balance - portfolio.initial_balance)
            / portfolio.initial_balance
            * 100
        ),
    }


def test_ema_rsi_walk_forward_windows_are_internally_consistent():
    """
    Walk-forward validation for the ema_rsi strategy: splits an
    8-regime synthetic history into rolling (train, test) windows and
    backtests each independently, instead of judging the strategy on
    one fixed period.

    ema_rsi has no fittable parameters, so this isn't classic
    "optimize on train, verify on test" walk-forward - it's an
    out-of-sample regime-robustness check: every window's backtest
    must produce internally consistent results (valid equity curve,
    metrics in sane ranges), and the strategy must actually trade
    somewhere across 8 very different regimes rather than only on a
    cherry-picked one.
    """

    df = _build_multi_regime_ohlcv()

    windows = WalkForwardAnalyzer(
        train_size=250,
        test_size=100,
    ).generate_windows(df)

    assert len(windows) >= 3

    results = []

    for i, (train_df, test_df) in enumerate(windows):

        train = _run_window(train_df)
        test = _run_window(test_df)

        results.append(
            {
                "window": i,
                "train": train,
                "test": test,
            }
        )

        for run in (train, test):

            history = run["portfolio"].balance_history

            assert history[0] == run["portfolio"].initial_balance
            assert history[-1] == run["portfolio"].balance
            assert all(np.isfinite(balance) for balance in history)

            assert 0 <= run["win_rate"] <= 100
            assert run["max_drawdown"] >= 0
            assert np.isfinite(run["return_pct"])

    print(
        "\nema_rsi walk-forward "
        "(train=250, test=100 candles, 8-regime synthetic data)"
    )
    print(
        f"{'win':>3} | "
        f"{'train trades':>12} {'train wr%':>9} {'train pf':>8} {'train ret%':>10} || "
        f"{'test trades':>11} {'test wr%':>8} {'test pf':>8} {'test ret%':>9}"
    )

    for r in results:

        tr, te = r["train"], r["test"]

        print(
            f"{r['window']:>3} | "
            f"{tr['trades']:>12} {tr['win_rate']:>9.1f} {tr['profit_factor']:>8.2f} {tr['return_pct']:>10.2f} || "
            f"{te['trades']:>11} {te['win_rate']:>8.1f} {te['profit_factor']:>8.2f} {te['return_pct']:>9.2f}"
        )

    total_trades = sum(
        r["train"]["trades"] + r["test"]["trades"]
        for r in results
    )

    print(f"total trades across all windows: {total_trades}")

    # The strategy must engage somewhere across 8 very different
    # regimes - if this is 0, the wiring is broken, not just "the
    # market didn't offer a setup".
    assert total_trades > 0
