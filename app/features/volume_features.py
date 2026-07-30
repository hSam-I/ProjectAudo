import pandas as pd


class VolumeFeatures:
    """
    Volume based AI features.
    """

    @staticmethod
    def build(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        df = df.copy()

        # ------------------------------------------
        # Average Volume
        # ------------------------------------------

        df["avg_volume"] = (
            df["volume"]
            .rolling(20)
            .mean()
        )

        # ------------------------------------------
        # Relative Volume (RVOL)
        # ------------------------------------------

        df["relative_volume"] = (
            df["volume"]
            / df["avg_volume"]
        )

        # ------------------------------------------
        # Volume Spike
        # ------------------------------------------

        df["volume_spike"] = (
            df["relative_volume"] > 2.0
        )

        # ------------------------------------------
        # VWAP Position
        # ------------------------------------------

        df["above_vwap"] = (
            df["close"]
            > df["vwap"]
        )

        # ------------------------------------------
        # Distance from VWAP
        # ------------------------------------------

        df["vwap_distance"] = (
            (
                df["close"]
                - df["vwap"]
            )
            / df["vwap"]
        )

        # ------------------------------------------
        # OBV Trend
        # ------------------------------------------

        df["obv_change"] = (
            df["obv"].diff()
        )

        df["obv_up"] = (
            df["obv_change"] > 0
        )

        df["obv_down"] = (
            df["obv_change"] < 0
        )

        return df