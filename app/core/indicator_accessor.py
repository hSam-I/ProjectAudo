class IndicatorAccessor:
    """
    Provides backward-compatible access
    to indicator values.

    This class hides indicator naming
    differences from the rest of the project.
    """

    @staticmethod
    def ema_fast(last):

        return last.get(
            "ema_fast",
            last.get("ema_20"),
        )

    @staticmethod
    def ema_slow(last):

        return last.get(
            "ema_slow",
            last.get("ema_50"),
        )

    @staticmethod
    def rsi(last):

        return last.get("rsi")

    @staticmethod
    def adx(last):

        return last.get("adx")

    @staticmethod
    def macd(last):

        return last.get("macd")

    @staticmethod
    def macd_signal(last):

        return last.get("macd_signal")

    @staticmethod
    def macd_histogram(last):

        return last.get(
            "macd_histogram",
            last.get("macd_hist"),
        )

    @staticmethod
    def atr(last):

        return last.get("atr")

    @staticmethod
    def close(last):

        return last.get("close")

    @staticmethod
    def high(last):

        return last.get("high")

    @staticmethod
    def low(last):

        return last.get("low")

    @staticmethod
    def volume(last):

        return last.get("volume")