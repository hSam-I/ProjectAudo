from app.backtesting.backtester import Backtester
from app.config.settings import settings


def test_backtester_runs(sample_market_data):

    portfolio = Backtester().run(sample_market_data.copy())

    assert portfolio is not None


def test_portfolio_created(sample_market_data):

    portfolio = Backtester().run(sample_market_data.copy())

    assert portfolio.initial_balance > 0


def test_balance_is_numeric(sample_market_data):

    portfolio = Backtester().run(sample_market_data.copy())

    assert isinstance(portfolio.balance, float)


def test_backtester_wires_settings_commission_and_slippage():
    """
    Regression: Backtester used to build PaperBroker with its own
    hardcoded fee/slippage defaults, so settings.commission and
    settings.slippage had zero effect on backtest results.
    """

    broker = Backtester().broker

    assert broker.fee_model.fee_rate == settings.commission
    assert broker.slippage_model.slippage_rate == settings.slippage


def test_backtester_commission_and_slippage_affect_balance(
    random_walk_ohlcv,
    monkeypatch,
):
    """
    Higher trading costs on the same price series/signals must
    leave less balance behind than lower trading costs -- proof
    that commission/slippage are actually applied, not just
    configured.
    """

    df = random_walk_ohlcv(n=500)

    monkeypatch.setattr(settings, "commission", 0.0)
    monkeypatch.setattr(settings, "slippage", 0.0)

    zero_cost_balance = Backtester().run(df.copy()).balance

    monkeypatch.setattr(settings, "commission", 0.02)
    monkeypatch.setattr(settings, "slippage", 0.01)

    high_cost_balance = Backtester().run(df.copy()).balance

    assert high_cost_balance < zero_cost_balance