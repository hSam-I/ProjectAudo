from app.optimization.monte_carlo import MonteCarloSimulator


def test_simulation():

    simulator = MonteCarloSimulator(
        [
            100,
            -50,
            75,
            25,
        ]
    )

    results = simulator.simulate(100)

    assert len(results) == 100


def test_average():

    simulator = MonteCarloSimulator(
        [
            100,
            -50,
            75,
            25,
        ]
    )

    average = simulator.average_result(100)

    assert isinstance(
        average,
        float,
    )


def test_best():

    simulator = MonteCarloSimulator(
        [
            100,
            -50,
            75,
            25,
        ]
    )

    best = simulator.best_result(100)

    assert isinstance(
        best,
        (int, float),
    )


def test_worst():

    simulator = MonteCarloSimulator(
        [
            100,
            -50,
            75,
            25,
        ]
    )

    worst = simulator.worst_result(100)

    assert isinstance(
        worst,
        (int, float),
    )