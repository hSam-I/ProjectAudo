from app.backtesting.backtester import Backtester
from app.backtesting.performance import PerformanceAnalyzer
from app.config.settings import settings
from app.data.binance_provider import BinanceProvider
from app.data.validator import DataValidator
from app.decision.decision_engine import DecisionEngine
from app.indicators.indicator_engine import IndicatorEngine
from app.web.charts import equity_chart


def load_dashboard_data():

    provider = BinanceProvider()

    df = provider.fetch_ohlcv(
        symbol=settings.symbol,
        timeframe=settings.timeframe,
        limit=settings.candle_limit,
    )

    if not DataValidator.validate(df):

        return {
            "price": 0,
            "raw_signal": "N/A",
            "signal": "N/A",
            "score": 0,
            "confidence": "N/A",
            "balance": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "max_drawdown": 0,
            "equity_chart": "",
            "trades": [],
        }

    df = IndicatorEngine.calculate_all(df)

    decision = DecisionEngine().evaluate(df)

    portfolio = Backtester().run(df)

    performance = PerformanceAnalyzer(portfolio)

    last = df.iloc[-1]

    return {

        "price": round(last["close"], 2),

        "raw_signal": decision.raw_signal,

        "signal": decision.signal,

        "score": decision.score,

        "confidence": decision.confidence,

        "balance": round(portfolio.balance, 2),

        "win_rate": round(
            performance.win_rate(),
            2,
        ),

        "profit_factor": round(
            performance.profit_factor(),
            2,
        ),

        "max_drawdown": round(
            performance.max_drawdown(),
            2,
        ),

        "equity_chart": equity_chart(
            portfolio.balance_history
        ),

        "trades": portfolio.trades,

    }