from app.optimization.risk_of_ruin import RiskOfRuinAnalyzer


def test_ruin_probability():

    analyzer = RiskOfRuinAnalyzer(
        [
            100,
            50,
            -20,
            -10,
            30,
        ]
    )

    assert analyzer.ruin_probability() == 0.4


def test_survival_probability():

    analyzer = RiskOfRuinAnalyzer(
        [
            100,
            50,
            -20,
            -10,
            30,
        ]
    )

    assert analyzer.survival_probability() == 0.6


def test_best_case():

    analyzer = RiskOfRuinAnalyzer(
        [
            100,
            50,
            -20,
            -10,
            30,
        ]
    )

    assert analyzer.best_case() == 100


def test_worst_case():

    analyzer = RiskOfRuinAnalyzer(
        [
            100,
            50,
            -20,
            -10,
            30,
        ]
    )

    assert analyzer.worst_case() == -20


def test_average():

    analyzer = RiskOfRuinAnalyzer(
        [
            100,
            50,
            -20,
            -10,
            30,
        ]
    )

    assert analyzer.average() == 30