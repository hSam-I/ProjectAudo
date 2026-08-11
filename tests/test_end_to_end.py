import numpy as np
import pandas as pd

from app.backtesting.backtester import Backtester
from app.backtesting.performance import PerformanceAnalyzer
from app.data.validator import DataValidator
from app.decision.decision_engine import DecisionEngine
from app.indicators.indicator_engine import IndicatorEngine
from app.risk.risk_manager import RiskManager


def _build_synthetic_ohlcv() -> pd.DataFrame:
    """
    Deterministic, four-phase OHLCV series designed so the default
    ema_rsi strategy actually trades on it:

    1. Downtrend (50 bars) - establishes ema_fast < ema_slow.
    2. Oscillating grind-up (90 bars) - lets ema_fast slowly cross
       above ema_slow while RSI stays out of overbought territory,
       so EMARSIStrategy's crossover condition (rsi < 70) can fire.
    3. Sustained rally (45 bars) - builds profit and flips the
       trend/breakout/volume AI features true.
    4. Sharp reversal down (45 bars) - forces the open trade to exit
       via stop-loss/trailing-stop instead of dangling open forever.
    """

    closes = []
    price = 100.0

    for _ in range(50):
        price -= 0.2
        closes.append(price)

    base = price

    for i in range(90):
        price = (
            base
            + 0.05 * i
            + 2.5 * np.sin(2 * np.pi * i / 24)
        )
        closes.append(price)

    for _ in range(45):
        price += 1.3
        closes.append(price)

    for _ in range(45):
        price -= 1.6
        closes.append(price)

    closes = np.array(closes)
    n = len(closes)

    deltas = np.diff(closes, prepend=closes[0])
    spread = np.clip(np.abs(deltas) * 1.5, 0.15, None)

    open_ = closes - deltas * 0.5
    high = np.maximum(open_, closes) + spread * 0.4
    low = np.minimum(open_, closes) - spread * 0.4

    volume = np.full(n, 1000.0)
    volume[50:185] *= 1.8

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


def test_end_to_end_pipeline_produces_a_consistent_backtest():
    """
    Runs the same data -> indicators -> decision -> risk -> backtest
    chain main.py runs, on fixed synthetic OHLCV data, and checks the
    result is internally consistent end to end (not just "doesn't crash").
    """

    raw_df = _build_synthetic_ohlcv()

    # ------------------------------------------------------
    # Data validation
    # ------------------------------------------------------

    assert DataValidator.validate(raw_df) is True

    # ------------------------------------------------------
    # Indicators + AI features
    # ------------------------------------------------------

    df = IndicatorEngine.calculate_all(raw_df.copy())

    assert "ema_fast" in df.columns
    assert "rsi" in df.columns
    assert "atr" in df.columns

    # ------------------------------------------------------
    # Decision
    # ------------------------------------------------------

    decision = DecisionEngine().evaluate(df)

    assert decision.signal is not None
    assert -100 <= decision.score <= 100
    assert decision.confidence in ("LOW", "MEDIUM", "HIGH")

    # ------------------------------------------------------
    # Risk
    # ------------------------------------------------------

    risk = RiskManager()

    last = df.iloc[-1]

    stop_loss = risk.stop_loss(last["close"], last["atr"])
    take_profit = risk.take_profit(last["close"], last["atr"])

    assert stop_loss < last["close"] < take_profit

    # ------------------------------------------------------
    # Backtest
    # ------------------------------------------------------

    portfolio = Backtester().run(raw_df.copy())

    # The engineered crossover + rally must have produced at least
    # one real trade - otherwise the strategy/decision wiring is broken.
    assert portfolio.total_trades >= 1
    assert portfolio.closed_trades_count >= 1

    # No trade should be left dangling forever in this scenario.
    assert (
        portfolio.open_trades
        == portfolio.total_trades - portfolio.closed_trades_count
    )

    # ------------------------------------------------------
    # Equity curve consistency
    # ------------------------------------------------------

    history = portfolio.balance_history

    assert history[0] == portfolio.initial_balance
    assert history[-1] == portfolio.balance

    assert all(np.isfinite(balance) for balance in history)

    # One balance snapshot is appended per closed trade.
    assert len(history) == portfolio.closed_trades_count + 1

    # ------------------------------------------------------
    # Performance metrics stay in sane ranges
    # ------------------------------------------------------

    performance = PerformanceAnalyzer(portfolio)

    assert 0 <= performance.win_rate() <= 100
    assert 0 <= performance.loss_rate() <= 100
    assert performance.max_drawdown() >= 0

    # ------------------------------------------------------
    # Trade sanity
    # ------------------------------------------------------

    for trade in portfolio.trades:
        assert trade.status == "CLOSED"
        assert trade.exit_price is not None
        assert trade.quantity > 0
        assert np.isfinite(trade.profit)
