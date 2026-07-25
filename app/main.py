from app.data.binance_provider import BinanceProvider
from app.data.validator import DataValidator
from app.indicators.indicator_engine import IndicatorEngine
from app.logging.logger import logger
from app.strategy.ema_rsi_strategy import EMARSIStrategy


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

    # Calculate all indicators
    df = IndicatorEngine.calculate_all(df)

    # Last candle
    last = df.iloc[-1]

    # Strategy
    strategy = EMARSIStrategy()
    signal = strategy.generate_signal(df)

    # Trend
    trend = (
        "BULLISH 🟢"
        if last["ema_20"] > last["ema_50"]
        else "BEARISH 🔴"
    )

    # RSI Status
    if last["rsi"] < 30:
        rsi_status = "OVERSOLD 🟢"
    elif last["rsi"] > 70:
        rsi_status = "OVERBOUGHT 🔴"
    else:
        rsi_status = "NEUTRAL 🟡"

    # MACD Status
    if last["macd_histogram"] > 0:
        macd_status = "BULLISH MOMENTUM 🟢"
    else:
        macd_status = "BEARISH MOMENTUM 🔴"

    # Report
    print()
    print("=" * 60)
    print("                    PROJECT AUDO")
    print("                 MARKET ANALYSIS")
    print("=" * 60)

    print(f"Current Price : {last['close']:.2f}")
    print(f"EMA 20        : {last['ema_20']:.2f}")
    print(f"EMA 50        : {last['ema_50']:.2f}")
    print(f"RSI           : {last['rsi']:.2f}")
    print(f"MACD          : {last['macd']:.2f}")
    print(f"MACD Signal   : {last['macd_signal']:.2f}")
    print(f"MACD Hist     : {last['macd_histogram']:.2f}")

    print("-" * 60)

    print(f"Trend         : {trend}")
    print(f"RSI Status    : {rsi_status}")
    print(f"MACD Status   : {macd_status}")

    print("-" * 60)

    print(f"Trading Signal: {signal}")

    print("=" * 60)


if __name__ == "__main__":
    main()