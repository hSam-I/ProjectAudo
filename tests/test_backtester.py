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


def test_backtester_starts_with_empty_portfolio_manager():

    backtester = Backtester()

    assert backtester.portfolio_manager.count() == 0


def test_portfolio_manager_stays_consistent_with_portfolio(random_walk_ohlcv):
    """
    Phase A (multi-position groundwork) replaced the single current_trade
    scalar with PortfolioManager (a symbol -> Trade dict) for the "is a
    position already open" gate, while the real Portfolio (balance/
    open_positions list) keeps doing the actual bookkeeping unchanged.
    The two must never disagree on how many positions are open.
    """

    backtester = Backtester()

    portfolio = backtester.run(random_walk_ohlcv())

    assert backtester.portfolio_manager.count() == portfolio.open_trades