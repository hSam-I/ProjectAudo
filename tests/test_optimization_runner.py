from app.optimization.optimization_runner import OptimizationRunner


def test_select_best():

    runner = OptimizationRunner()

    results = [
        {
            "profit_factor": 1.2,
            "parameters": {
                "ema": 10,
            },
        },
        {
            "profit_factor": 2.4,
            "parameters": {
                "ema": 20,
            },
        },
        {
            "profit_factor": 1.8,
            "parameters": {
                "ema": 50,
            },
        },
    ]

    best = runner.select_best(results)

    assert best["profit_factor"] == 2.4
    assert best["parameters"]["ema"] == 20