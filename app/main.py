import json
from pathlib import Path

from app.backtesting.backtester import Backtester
from app.backtesting.performance import PerformanceAnalyzer
from app.config.settings import settings
from app.data.binance_provider import BinanceProvider
from app.data.exceptions import DataProviderError
from app.data.validator import DataValidator
from app.decision.decision_engine import DecisionEngine
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


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--walk-forward",
        action="store_true",
        help="Run rolling train/test walk-forward backtests instead of a single run.",
    )

    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan settings.symbols for raw signals instead of running a single-symbol backtest.",
    )

    args = parser.parse_args()

    if args.walk_forward:
        run_walk_forward()
    elif args.scan:
        run_scan()
    else:
        main()