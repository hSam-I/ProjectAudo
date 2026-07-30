from app.backtesting.backtester import Backtester
from app.backtesting.performance import PerformanceAnalyzer
from app.config.settings import settings
from app.data.binance_provider import BinanceProvider
from app.data.validator import DataValidator
from app.decision.decision_engine import DecisionEngine
from app.indicators.indicator_engine import IndicatorEngine
from app.logging.logger import logger
from app.reporting.drawdown_chart import DrawdownChart
from app.reporting.equity_chart import EquityChart
from app.reporting.equity_report import EquityReport
from app.reporting.trade_distribution_chart import TradeDistributionChart
from app.reporting.trade_journal import TradeJournal
from app.risk.risk_manager import RiskManager


def print_separator():
    print("-" * 70)


def main():

    provider = BinanceProvider()

    df = provider.fetch_ohlcv(
        symbol=settings.symbol,
        timeframe=settings.timeframe,
        limit=settings.candle_limit,
    )

    if not DataValidator.validate(df):
        logger.error("Invalid market data")
        return

    logger.info("Market data received successfully")

    df = IndicatorEngine.calculate_all(df)

    decision = DecisionEngine().evaluate(df)

    last = df.iloc[-1]

    risk = RiskManager()

    balance = settings.starting_balance

    risk_amount = risk.risk_amount(balance)

    stop_loss = risk.stop_loss(last["close"], last["atr"])

    take_profit = risk.take_profit(last["close"], last["atr"])

    portfolio = Backtester().run(df)

    # ==========================
    # REPORTS
    # ==========================

    TradeJournal().export(portfolio)

    EquityReport().export(portfolio)

    EquityChart().export(portfolio)

    DrawdownChart().export(portfolio)

    TradeDistributionChart().export(portfolio)


    performance = PerformanceAnalyzer(portfolio)

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

    print_separator()

    print(f"Raw Signal    : {decision.raw_signal}")
    print(f"Final Signal  : {decision.signal}")
    print(f"Score         : {decision.score}/100")
    print(f"Confidence    : {decision.confidence}")

    print_separator()

    print("Reasons")

    for reason in decision.reasons:
        print(f"  ✓ {reason}")

    print_separator()

    print(f"Balance       : ${balance:,.2f}")
    print(f"Risk Amount   : ${risk_amount:,.2f}")
    print(f"Stop Loss     : {stop_loss:.2f}")
    print(f"Take Profit   : {take_profit:.2f}")

    print_separator()

    print("Backtesting")

    print(f"Total Trades  : {portfolio.total_trades}")
    print(f"Closed Trades : {portfolio.closed_trades}")
    print(f"Open Trades   : {portfolio.open_trades}")
    print(f"Balance       : ${portfolio.balance:,.2f}")

    print_separator()

    print("Performance")

    print(f"Win Rate      : {performance.win_rate():.2f}%")
    print(f"Loss Rate     : {performance.loss_rate():.2f}%")
    print(f"Average Win   : ${performance.average_win():,.2f}")
    print(f"Average Loss  : -${abs(performance.average_loss()):,.2f}")
    print(f"Largest Win   : ${performance.largest_win():,.2f}")
    print(f"Largest Loss  : -${abs(performance.largest_loss()):,.2f}")
    print(f"Gross Profit  : ${performance.gross_profit():,.2f}")
    print(f"Gross Loss    : ${performance.gross_loss():,.2f}")
    print(f"Profit Factor : {performance.profit_factor():.2f}")
    print(f"Expectancy    : ${performance.expectancy():,.2f}")
    print(f"Peak Equity   : ${performance.peak_equity():,.2f}")
    print(f"Current Equity: ${portfolio.balance:,.2f}")
    print(f"Max Drawdown  : {performance.max_drawdown():.2f}%")

    print_separator()

    print("Trade History")
    print(portfolio.trade_history())

    print("=" * 70)


if __name__ == "__main__":
    main()