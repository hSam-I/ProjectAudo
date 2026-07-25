from app.data.binance_provider import BinanceProvider
from app.data.validator import DataValidator
from app.indicators.indicator_engine import IndicatorEngine
from app.strategy.ema_rsi_strategy import EMARSIStrategy
from app.risk.risk_manager import RiskManager
from app.decision.signal_scorer import SignalScorer


class MarketAnalyzer:

    def analyze(self):

        provider = BinanceProvider()

        df = provider.fetch_ohlcv(
            symbol="BTC/USDT",
            timeframe="1h",
            limit=100,
        )

        if not DataValidator.validate(df):
            return None

        df = IndicatorEngine.calculate_all(df)

        strategy = EMARSIStrategy()

        signal = strategy.generate_signal(df)

        score, confidence, reasons = SignalScorer.score(df)

        last = df.iloc[-1]

        risk = RiskManager()

        balance = 10000

        return {
            "df": df,
            "last": last,
            "signal": signal,
            "score": score,
            "confidence": confidence,
            "reasons": reasons,
            "balance": balance,
            "risk_amount": risk.risk_amount(balance),
            "stop_loss": risk.stop_loss(last["close"], last["atr"]),
            "take_profit": risk.take_profit(last["close"], last["atr"]),
        }