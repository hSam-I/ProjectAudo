from app.core.enums import Signal
from app.voting.strategy_vote import StrategyVote
from app.voting.voting_engine import VotingEngine


def test_weighted_buy():

    votes = [
        StrategyVote("ema", Signal.BUY, 1.50),
        StrategyVote("trend", Signal.BUY, 1.25),
        StrategyVote("breakout", Signal.SELL, 0.75),
    ]

    assert VotingEngine.vote(votes) == Signal.BUY


def test_weighted_sell():

    votes = [
        StrategyVote("ema", Signal.SELL, 1.50),
        StrategyVote("trend", Signal.SELL, 1.25),
        StrategyVote("breakout", Signal.BUY, 0.75),
    ]

    assert VotingEngine.vote(votes) == Signal.SELL


def test_weighted_hold():

    votes = [
        StrategyVote("ema", Signal.BUY, 1.0),
        StrategyVote("trend", Signal.SELL, 1.0),
    ]

    assert VotingEngine.vote(votes) == Signal.HOLD