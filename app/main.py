from app.data.binance_provider import BinanceProvider
from app.data.validator import DataValidator

from app.indicators.indicator_engine import IndicatorEngine

from app.strategy.ema_rsi_strategy import EMARSIStrategy

from app.risk.risk_manager import RiskManager

from app.decision.signal_scorer import SignalScorer

from app.backtesting.backtester import Backtester

from app.logging.logger import logger


def main():

    provider = BinanceProvider()

    df = provider.fetch_ohlcv(
        symbol="BTC/USDT",
        timeframe="1h",
        limit=100,
    )

    if not DataValidator.validate(df):
        logger.error("Invalid market data")
        return

    logger.info("Market data received successfully")

    # Calculate indicators
    df = IndicatorEngine.calculate_all(df)

    # Latest candle
    last = df.iloc[-1]

    # Strategy
    strategy = EMARSIStrategy()
    signal = strategy.generate_signal(df)

    # Signal score
    score, confidence, reasons = SignalScorer.score(df)

    # Risk
    risk = RiskManager()

    balance = 10000

    risk_amount = risk.risk_amount(balance)

    stop_loss = risk.stop_loss(
        last["close"],
        last["atr"],
    )

    take_profit = risk.take_profit(
        last["close"],
        last["atr"],
    )

    # Backtest
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

    print("-" * 70)

    print(f"Signal        : {signal}")
    print(f"Score         : {score}/100")
    print(f"Confidence    : {confidence}")

    print("-" * 70)

    print("Reasons")

    for reason in reasons:
        print(f"  ✓ {reason}")

    print("-" * 70)

    print(f"Balance       : ${balance:,.2f}")
    print(f"Risk Amount   : ${risk_amount:,.2f}")
    print(f"Stop Loss     : {stop_loss:.2f}")
    print(f"Take Profit   : {take_profit:.2f}")

    print("-" * 70)

    print("Backtesting")

    print(f"Trades        : {portfolio.total_trades}")
    print(f"Balance       : ${portfolio.balance:,.2f}")

    print("=" * 70)


if __name__ == "__main__":
    main()