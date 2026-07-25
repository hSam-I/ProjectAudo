from app.backtesting.backtester import Backtester
from app.config.settings import settings
from app.data.binance_provider import BinanceProvider
from app.data.validator import DataValidator
from app.decision.signal_scorer import SignalScorer
from app.indicators.indicator_engine import IndicatorEngine
from app.logging.logger import logger
from app.risk.risk_manager import RiskManager
from app.strategy.ema_rsi_strategy import EMARSIStrategy


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

    strategy = EMARSIStrategy()

    signal = strategy.generate_signal(df)

    score, confidence, reasons = SignalScorer.score(df)

    last = df.iloc[-1]

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

    backtester = Backtester()

    portfolio = backtester.run(df)

    print()
    print("=" * 70)
    print("                    PROJECT AUDO")
    print("                 AI MARKET REPORT")
    print("=" * 70)

    print(f"Current Price : {last['close']:.2f}")
    print(f"EMA20         : {last['ema_20']:.2f}")
    print(f"EMA50         : {last['ema_50']:.2f}")
    print(f"RSI           : {last['rsi']:.2f}")
    print(f"MACD          : {last['macd']:.2f}")
    print(f"ATR           : {last['atr']:.2f}")

    print_separator()

    print(f"Signal        : {signal}")
    print(f"Score         : {score}/100")
    print(f"Confidence    : {confidence}")

    print_separator()

    print("Reasons")

    for reason in reasons:
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

    print("Trade History")
    print(portfolio.trade_history())

    print("=" * 70)


if __name__ == "__main__":
    main()