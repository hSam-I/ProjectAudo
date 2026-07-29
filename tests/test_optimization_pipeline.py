from app.optimization.optimization_pipeline import OptimizationPipeline


def test_store_result():

    pipeline = OptimizationPipeline()

    pipeline.add_result(
        parameters={
            "ema_fast": 20,
            "ema_slow": 50,
        },
        metrics={
            "profit_factor": 2.1,
            "win_rate": 62,
        },
    )

    assert len(pipeline.results) == 1

    assert (
        pipeline.results[0]["metrics"]["profit_factor"]
        == 2.1
    )


def test_best_result():

    pipeline = OptimizationPipeline()

    pipeline.add_result(
        parameters={
            "ema_fast": 10,
        },
        metrics={
            "profit_factor": 1.4,
        },
    )

    pipeline.add_result(
        parameters={
            "ema_fast": 20,
        },
        metrics={
            "profit_factor": 2.3,
        },
    )

    pipeline.add_result(
        parameters={
            "ema_fast": 30,
        },
        metrics={
            "profit_factor": 1.8,
        },
    )

    best = pipeline.best()

    assert best["parameters"]["ema_fast"] == 20

    assert (
        best["metrics"]["profit_factor"]
        == 2.3
    )