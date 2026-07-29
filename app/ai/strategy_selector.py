from app.ai.market_regime import MarketRegime


class StrategySelector:

    @staticmethod
    def choose(df):

        regime = MarketRegime.detect(df)

        if regime == "TREND":
            return "trend_following"

        if regime == "RANGE":
            return "mean_reversion"

        if regime == "BREAKOUT":
            return "breakout"

        return "ema_rsi"