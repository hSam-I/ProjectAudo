from app.backtesting.backtester import Backtester


def test_backtester_runs(sample_market_data):

    portfolio = Backtester().run(sample_market_data.copy())

    assert portfolio is not None


def test_portfolio_created(sample_market_data):

    portfolio = Backtester().run(sample_market_data.copy())

    assert portfolio.initial_balance > 0


def test_balance_is_numeric(sample_market_data):

    portfolio = Backtester().run(sample_market_data.copy())

    assert isinstance(portfolio.balance, float)