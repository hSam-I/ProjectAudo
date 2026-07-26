from pathlib import Path

from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.reporting.trade_journal import TradeJournal


def test_trade_journal_export(tmp_path):

    portfolio = Portfolio(10000)

    trade = Trade(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=100,
        quantity=1,
        entry_time="2026-01-01",

        stop_loss=95,
        take_profit=110,
        risk_amount=100,
    )

    trade.close(
        exit_price=110,
        exit_time="2026-01-02",
        reason="TAKE_PROFIT",
    )

    portfolio.open_trade(trade)

    journal = TradeJournal()

    journal.filepath = tmp_path / "trade_history.csv"

    journal.export(portfolio)

    assert journal.filepath.exists()

    content = journal.filepath.read_text()

    assert "BTCUSDT" in content
    assert "TAKE_PROFIT" in content