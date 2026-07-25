import pandas as pd


class SignalScorer:

    @staticmethod
    def score(df: pd.DataFrame):

        last = df.iloc[-1]

        score = 0

        reasons = []

        # EMA
        if last["ema_20"] > last["ema_50"]:
            score += 30
            reasons.append("EMA Bullish")

        else:
            reasons.append("EMA Bearish")

        # RSI
        if last["rsi"] < 30:
            score += 25
            reasons.append("RSI Oversold")

        elif last["rsi"] > 70:
            reasons.append("RSI Overbought")

        else:
            score += 10
            reasons.append("RSI Neutral")

        # MACD
        if last["macd_histogram"] > 0:
            score += 20
            reasons.append("MACD Bullish")

        else:
            reasons.append("MACD Bearish")

        # ATR
        if last["atr"] > 0:
            score += 10
            reasons.append("ATR Valid")

        confidence = "LOW"

        if score >= 75:
            confidence = "HIGH"

        elif score >= 50:
            confidence = "MEDIUM"

        return score, confidence, reasons