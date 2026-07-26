from app.strategy.base_strategy import BaseStrategy


class EMARSIStrategy(BaseStrategy):

    def generate_signal(self, df):

        # En az iki mum gerekli
        if len(df) < 2:
            return "HOLD"

        previous = df.iloc[-2]
        current = df.iloc[-1]

        prev_ema20 = previous["ema_20"]
        prev_ema50 = previous["ema_50"]

        ema20 = current["ema_20"]
        ema50 = current["ema_50"]

        rsi = current["rsi"]

        # EMA20 aşağıdan yukarı geçti
        if (
            prev_ema20 <= prev_ema50
            and ema20 > ema50
            and rsi < 70
        ):
            return "BUY"

        # EMA20 yukarıdan aşağı geçti
        if (
            prev_ema20 >= prev_ema50
            and ema20 < ema50
            and rsi > 30
        ):
            return "SELL"

        return "HOLD"