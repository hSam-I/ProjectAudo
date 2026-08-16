import json
from pathlib import Path

from app.backtesting.backtester import Backtester
from app.backtesting.performance import PerformanceAnalyzer
from app.config.settings import settings
from app.data.binance_provider import BinanceProvider
from app.data.exceptions import DataProviderError
from app.data.multi_data_provider import MultiDataProvider
from app.data.validator import DataValidator
from app.decision.decision_engine import DecisionEngine
from app.execution.live_trader import LiveTrader
from app.features.feature_engine import FeatureEngine
from app.indicators.indicator_engine import IndicatorEngine
from app.logging.logger import logger
from app.optimization.walk_forward import WalkForwardAnalyzer
from app.reporting.drawdown_chart import DrawdownChart
from app.reporting.equity_chart import EquityChart
from app.reporting.equity_report import EquityReport
from app.reporting.trade_distribution_chart import TradeDistributionChart
from app.reporting.trade_journal import TradeJournal
from app.research.report_builder import ResearchReportBuilder
from app.research.research_engine import ResearchEngine
from app.risk.risk_manager import RiskManager
from app.scheduler.scheduler import Scheduler
from app.web.live_status_data import load_live_status


def separator():
    print("-" * 70)


def main():

    provider = BinanceProvider()

    try:

        df = provider.fetch_ohlcv(
            symbol=settings.symbols[0],
            timeframe=settings.timeframe,
            limit=settings.candle_limit,
        )

    except DataProviderError as e:

        logger.error(f"Failed to fetch market data: {e}")

        return

    if not DataValidator.validate(df):
        logger.error("Invalid market data")
        return

    logger.info("Market data received successfully")

    # =====================================================
    # Indicators
    # =====================================================

    df = IndicatorEngine.calculate_all(df)

    # =====================================================
    # AI Features
    # =====================================================

    df = FeatureEngine.build(df)

    # =====================================================
    # Decision
    # =====================================================

    decision = DecisionEngine().evaluate(df)

    last = df.iloc[-1]

    # =====================================================
    # Risk
    # =====================================================

    risk = RiskManager()

    balance = settings.starting_balance

    risk_amount = risk.risk_amount(balance)

    stop_loss = risk.stop_loss(
        last["close"],
        last["atr"],
    )

    take_profit = risk.take_profit(
        last["close"],
        last["atr"],
    )

    # =====================================================
    # Backtest
    # =====================================================

    portfolio = Backtester().run(df)

    performance = PerformanceAnalyzer(portfolio)

    # =====================================================
    # Reports
    # =====================================================

    TradeJournal().export(portfolio)

    EquityReport().export(portfolio)

    EquityChart().export(portfolio)

    DrawdownChart().export(portfolio)

    TradeDistributionChart().export(portfolio)

    # =====================================================
    # Research (optional)
    # =====================================================

    if settings.enable_research:

        profits = [
            trade.profit
            for trade in portfolio.closed_trades
        ]

        research_results = ResearchEngine().run(
            profits,
            df,
        )

        research_report = ResearchReportBuilder.build(
            research_results
        )

        Path("reports").mkdir(exist_ok=True)

        with open(
            Path("reports") / "research_report.json",
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(research_report, file, indent=2)

        logger.info(
            "Research report written to reports/research_report.json"
        )

    # =====================================================
    # Console Output
    # =====================================================

    print()

    print("=" * 70)
    print("                    PROJECT AUDO")
    print("                 AI MARKET REPORT")
    print("=" * 70)

    print(f"Current Price : {last['close']:.2f}")
    print(f"EMA Fast      : {last['ema_fast']:.2f}")
    print(f"EMA Slow      : {last['ema_slow']:.2f}")
    print(f"RSI           : {last['rsi']:.2f}")
    print(f"MACD          : {last['macd']:.2f}")
    print(f"ATR           : {last['atr']:.2f}")

    separator()

    print(f"Raw Signal    : {decision.raw_signal}")
    print(f"Final Signal  : {decision.signal}")
    print(f"Score         : {decision.score}/100")
    print(f"Confidence    : {decision.confidence}")
    print(f"Regime        : {decision.regime}")

    separator()

    print("Reasons")

    for reason in decision.reasons:
        print(f"  ✓ {reason}")

    separator()

    print(f"Balance       : ${balance:,.2f}")
    print(f"Risk Amount   : ${risk_amount:,.2f}")
    print(f"Stop Loss     : {stop_loss:.2f}")
    print(f"Take Profit   : {take_profit:.2f}")

    separator()

    print("Backtesting")

    print(f"Total Trades  : {portfolio.total_trades}")
    print(f"Open Trades   : {portfolio.open_trades}")
    print(f"Balance       : ${portfolio.balance:,.2f}")

    separator()

    print("Performance")

    print(f"Win Rate      : {performance.win_rate():.2f}%")
    print(f"Loss Rate     : {performance.loss_rate():.2f}%")
    print(f"Average Win   : ${performance.average_win():,.2f}")
    print(f"Average Loss  : ${performance.average_loss():,.2f}")
    print(f"Largest Win   : ${performance.largest_win():,.2f}")
    print(f"Largest Loss  : ${performance.largest_loss():,.2f}")
    print(f"Gross Profit  : ${performance.gross_profit():,.2f}")
    print(f"Gross Loss    : ${performance.gross_loss():,.2f}")
    print(f"Profit Factor : {performance.profit_factor():.2f}")
    print(f"Expectancy    : ${performance.expectancy():,.2f}")
    print(f"Peak Equity   : ${performance.peak_equity():,.2f}")
    print(f"Current Equity: ${portfolio.balance:,.2f}")
    print(f"Max Drawdown  : {performance.max_drawdown():.2f}%")
    print(f"CAGR          : {performance.cagr() * 100:.2f}%")
    print(f"Sharpe Ratio  : {performance.sharpe_ratio():.2f}")
    print(f"Sortino Ratio : {performance.sortino_ratio():.2f}")
    print(f"Calmar Ratio  : {performance.calmar_ratio():.2f}")

    separator()

    print("Trade History")

    history = portfolio.trade_history()

    if history:
        print(history)
    else:
        print("No trades.")

    print("=" * 70)


def run_walk_forward():
    """
    Rolling train/test backtest over WalkForwardAnalyzer windows.

    ema_rsi (and the other bundled strategies) have no fittable
    parameters, so this is a regime-robustness check rather than
    classic "optimize on train, verify on test" walk-forward - see
    tests/test_ema_rsi_walk_forward.py, whose pattern this productionizes.
    """

    provider = BinanceProvider()

    try:

        df = provider.fetch_ohlcv(
            symbol=settings.symbols[0],
            timeframe=settings.timeframe,
            limit=settings.candle_limit,
        )

    except DataProviderError as e:

        logger.error(f"Failed to fetch market data: {e}")

        return

    if not DataValidator.validate(df):
        logger.error("Invalid market data")
        return

    windows = WalkForwardAnalyzer(
        train_size=settings.walk_forward_train_size,
        test_size=settings.walk_forward_test_size,
    ).generate_windows(df)

    if not windows:
        logger.warning(
            "Not enough candles for a single walk-forward window "
            f"(need >= {settings.walk_forward_train_size + settings.walk_forward_test_size}, "
            f"got {len(df)})"
        )
        return

    print()
    print("=" * 70)
    print("            PROJECT AUDO - WALK-FORWARD REPORT")
    print("=" * 70)

    for i, (train_df, test_df) in enumerate(windows):

        train_portfolio = Backtester().run(
            train_df.reset_index(drop=True)
        )

        test_portfolio = Backtester().run(
            test_df.reset_index(drop=True)
        )

        train_performance = PerformanceAnalyzer(train_portfolio)
        test_performance = PerformanceAnalyzer(test_portfolio)

        print(f"Window {i}")

        print(
            f"  Train: trades={train_portfolio.closed_trades_count:<4} "
            f"win_rate={train_performance.win_rate():6.2f}% "
            f"profit_factor={train_performance.profit_factor():6.2f} "
            f"max_drawdown={train_performance.max_drawdown():6.2f}%"
        )

        print(
            f"  Test : trades={test_portfolio.closed_trades_count:<4} "
            f"win_rate={test_performance.win_rate():6.2f}% "
            f"profit_factor={test_performance.profit_factor():6.2f} "
            f"max_drawdown={test_performance.max_drawdown():6.2f}%"
        )

    print("=" * 70)


def run_scan():
    """
    Multi-symbol signal scan: Scheduler -> MultiAssetBacktester ->
    MultiDataProvider -> MarketScanner -> DecisionEngine.evaluate,
    one Decision per settings.symbols entry.

    This does NOT size positions or open trades - MarketScanner has no
    RiskManager/PaperBroker in its path, so it only reports what each
    symbol's DecisionEngine would decide right now. Use `main()` for
    the actual single-symbol paper-trading backtest.
    """

    try:

        decisions = Scheduler().run_once()

    except DataProviderError as e:

        logger.error(f"Failed to fetch market data during scan: {e}")

        return

    print()
    print("=" * 70)
    print("              PROJECT AUDO - MARKET SCAN")
    print("=" * 70)

    for symbol, decision in decisions.items():

        print(
            f"{symbol:<12} | "
            f"raw={decision.raw_signal:<5} | "
            f"signal={decision.signal:<5} | "
            f"score={decision.score:>4} | "
            f"confidence={decision.confidence:<6} | "
            f"regime={decision.regime}"
        )

    print("=" * 70)


def run_multi_position():
    """
    Multi-symbol backtest sharing one Portfolio's balance and risk
    limits across settings.symbols (Backtester.run() with a dict
    input - see the multi-position work on
    feature/multi-position-backtester). Unlike --scan, this actually
    opens/manages/closes trades through PaperBroker; it is a real
    backtest, not a signal-only scan.

    Sets settings.enable_multi_position=True for the duration of this
    call - Backtester.run() refuses a dict input otherwise, as a
    safety rail against any other code path accidentally triggering a
    multi-position run.
    """

    settings.enable_multi_position = True

    try:

        market_data = MultiDataProvider().fetch_all(
            symbols=settings.symbols,
            timeframe=settings.timeframe,
            limit=settings.candle_limit,
        )

    except DataProviderError as e:

        logger.error(f"Failed to fetch market data: {e}")

        return

    portfolio = Backtester().run(market_data)

    performance = PerformanceAnalyzer(portfolio)

    print()
    print("=" * 70)
    print("          PROJECT AUDO - MULTI-POSITION BACKTEST")
    print("=" * 70)

    print(f"Symbols       : {', '.join(settings.symbols)}")
    print(f"Total Trades  : {portfolio.total_trades}")
    print(f"Open Trades   : {portfolio.open_trades}")
    print(f"Balance       : ${portfolio.balance:,.2f}")

    separator()

    print("Performance")

    print(f"Win Rate      : {performance.win_rate():.2f}%")
    print(f"Loss Rate     : {performance.loss_rate():.2f}%")
    print(f"Profit Factor : {performance.profit_factor():.2f}")
    print(f"Expectancy    : ${performance.expectancy():,.2f}")
    print(f"Max Drawdown  : {performance.max_drawdown():.2f}%")
    print(f"Sharpe Ratio  : {performance.sharpe_ratio():.2f}")

    separator()

    print("Per-Symbol Trade Counts")

    trades_per_symbol = {}

    for trade in portfolio.trades:
        trades_per_symbol[trade.symbol] = (
            trades_per_symbol.get(trade.symbol, 0) + 1
        )

    for symbol in settings.symbols:
        print(f"  {symbol:<12}: {trades_per_symbol.get(symbol, 0)} trades")

    print("=" * 70)


def run_live_paper_trading():
    """
    Starts an indefinite live loop for settings.symbols[0].

    settings.enable_live_paper_trading controls what LiveTrader
    actually does (see its docstring) - default False means OBSERVE
    ONLY (no Backtester/PaperBroker is ever touched); True engages
    real paper trading through Backtester._step(). Deliberately NOT
    auto-enabled by this entrypoint the way --multi-position
    auto-enables its own flag - opening (paper) positions is high
    enough stakes that it requires an explicit settings/.env opt-in on
    top of `--live`, not just the CLI flag alone.
    """

    symbol = settings.symbols[0]

    trader = LiveTrader(symbol)

    try:

        trader.run_forever()

    except KeyboardInterrupt:

        logger.info(f"{symbol}: live loop stopped by user")


def run_web_server():
    """
    Starts the FastAPI dashboard + read-only live-status hub, blocking
    like --live does. uvicorn and app.web.server are imported lazily,
    inside this function rather than at module top - app.web.server
    imports app.web.dashboard_data, which pulls in Backtester/
    BinanceProvider/ScoreEngine; --live's startup path (and every other
    CLI mode) has no reason to pay that import cost just to run
    argparse dispatch.
    """

    import uvicorn

    from app.web.server import app as web_app

    uvicorn.run(
        web_app,
        host=settings.web_host,
        port=settings.web_port,
    )


def run_live_status():
    """
    One-shot console summary of load_live_status() - the same
    network-free read layer the /live web route uses to show what a
    separately running --live/--web process last wrote to disk.
    """

    status = load_live_status()

    print()
    print("=" * 70)
    print("              PROJECT AUDO - LIVE STATUS")
    print("=" * 70)

    if not status["has_run"]:

        print("No live process has run yet.")
        print("Start one with: python -m app.main --live")
        print("=" * 70)

        return

    if status["corrupt"]:

        print("Live state is corrupt:")
        print(f"  {status['corrupt_error']}")
        print("=" * 70)

        return

    health = status["health"]

    if health == "OVERDUE":
        health = f"OVERDUE (by {status['overdue_by_seconds']:.0f}s)"

    print(f"Symbol           : {status['symbol']}")
    print(f"Mode             : {status['mode']}")
    print(f"Health           : {health}")
    print(f"Started At       : {status['started_at']}")
    print(f"Restart Count    : {status['restart_count']}")
    print(f"Poll Count       : {status['poll_count']}")
    print(f"Error Count      : {status['error_count']}")
    print(f"Last Poll At     : {status['last_poll_at'] or '-'}")
    print(f"Next Poll Due At : {status['next_poll_due_at'] or '-'}")
    print(f"Last Error       : {status['last_error'] or '-'}")

    separator()

    if status["paper_trading"]:

        balance = status["balance"]

        print(
            f"Balance          : ${balance:,.2f}"
            if balance is not None
            else "Balance          : -"
        )
        print(f"Open Positions   : {status['open_position_count']}")

    else:

        print("Observation mode - no trades opened.")

    separator()

    print("Recent Decisions")

    if status["decisions"]:

        for decision in status["decisions"]:

            print(
                f"  {decision['timestamp']} | {decision['symbol']} | "
                f"raw={decision['raw_signal']} | final={decision['signal']} | "
                f"score={decision['score']} | regime={decision['regime']}"
            )

    else:

        print("  (none logged yet)")

    print("=" * 70)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    # A single mutually-exclusive group so combining two mode flags
    # (e.g. `--live --web`) is a hard argparse error instead of one
    # flag silently losing to if/elif priority order.
    mode = parser.add_mutually_exclusive_group()

    mode.add_argument(
        "--walk-forward",
        action="store_true",
        help="Run rolling train/test walk-forward backtests instead of a single run.",
    )

    mode.add_argument(
        "--scan",
        action="store_true",
        help="Scan settings.symbols for raw signals instead of running a single-symbol backtest.",
    )

    mode.add_argument(
        "--multi-position",
        action="store_true",
        help="Run a multi-symbol backtest across settings.symbols sharing one portfolio's risk limits.",
    )

    mode.add_argument(
        "--live",
        action="store_true",
        help="Start an indefinite live loop for settings.symbols[0] (OBSERVE ONLY for now - no trades).",
    )

    mode.add_argument(
        "--web",
        action="store_true",
        help="Start the FastAPI dashboard + read-only live-status hub instead of running a backtest.",
    )

    mode.add_argument(
        "--live-status",
        action="store_true",
        help="Print a one-shot summary of a separately running --live/--web process's on-disk status.",
    )

    args = parser.parse_args()

    if args.walk_forward:
        run_walk_forward()
    elif args.scan:
        run_scan()
    elif args.multi_position:
        run_multi_position()
    elif args.live:
        run_live_paper_trading()
    elif args.web:
        run_web_server()
    elif args.live_status:
        run_live_status()
    else:
        main()