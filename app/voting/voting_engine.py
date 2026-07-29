from app.core.enums import Signal


class VotingEngine:
    """
    Combines weighted strategy votes into a final signal.
    """

    @staticmethod
    def vote(votes):

        buy_weight = 0.0
        sell_weight = 0.0

        for vote in votes:

            if vote.signal == Signal.BUY:
                buy_weight += vote.weight

            elif vote.signal == Signal.SELL:
                sell_weight += vote.weight

        if buy_weight > sell_weight:
            return Signal.BUY

        if sell_weight > buy_weight:
            return Signal.SELL

        return Signal.HOLD