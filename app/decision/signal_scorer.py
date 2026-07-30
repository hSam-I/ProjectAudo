from app.core.indicator_accessor import IndicatorAccessor


class SignalScorer:

    @staticmethod
    def score(df):

        last = df.iloc[-1]

        score = 0
        reasons = []

        ema_fast = IndicatorAccessor.ema_fast(last)
        ema_slow = IndicatorAccessor.ema_slow(last)

        rsi = IndicatorAccessor.rsi(last)

        macd = IndicatorAccessor.macd(last)
        macd_signal = IndicatorAccessor.macd_signal(last)

        adx = IndicatorAccessor.adx(last)

        if ema_fast is not None and ema_slow is not None:
            if ema_fast > ema_slow:
                score += 20
                reasons.append("EMA Trend Bullish")
            else:
                score -= 20
                reasons.append("EMA Trend Bearish")

        if rsi is not None:
            if rsi > 55:
                score += 15
                reasons.append("RSI Bullish")

            elif rsi < 45:
                score -= 15
                reasons.append("RSI Bearish")

        if (
            macd is not None
            and macd_signal is not None
        ):
            if macd > macd_signal:
                score += 15
                reasons.append("MACD Bullish")

            else:
                score -= 15
                reasons.append("MACD Bearish")

        if adx is not None and adx > 25:
            score += 10
            reasons.append("Strong Trend")

        confidence = "LOW"

        if score >= 60:
            confidence = "HIGH"

        elif score >= 30:
            confidence = "MEDIUM"

        return score, confidence, reasons