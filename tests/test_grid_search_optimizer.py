from app.optimization.grid_search_optimizer import (
    GridSearchOptimizer,
)


def fake_evaluator(parameters):

    return {
        "profit_factor": parameters["ema_fast"] / 10,
    }


def test_grid_search_optimizer():

    optimizer = GridSearchOptimizer()

    best = optimizer.optimize(
        parameter_sets=[
            {
                "ema_fast": 10,
            },
            {
                "ema_fast": 30,
            },
            {
                "ema_fast": 20,
            },
        ],
        evaluator=fake_evaluator,
    )

    assert best["parameters"]["ema_fast"] == 30

    assert (
        best["metrics"]["profit_factor"]
        == 3.0
    )