
import pandas as pd
import pytest

from analysis import calculate_metrics



def test_metrics_calculation():
    matched = pd.DataFrame({
        "actual_mw": [100, 200, 300],
        "forecast_mw": [110, 180, 330],
    })

    metrics = calculate_metrics(matched)

    assert metrics["matched_hours"] == 3
    assert metrics["bias_mw"] == pytest.approx(20 / 3)
    assert metrics["mae_mw"] == pytest.approx(20)
    assert metrics["rmse_mw"] == pytest.approx(
        (1400 / 3) ** 0.5
    )



def test_overestimation_has_positive_bias():
    matched = pd.DataFrame({
        "actual_mw": [100, 200],
        "forecast_mw": [120, 220],
    })

    metrics = calculate_metrics(matched)

    assert metrics["bias_mw"] > 0


def test_underestimation_has_negative_bias():
    matched = pd.DataFrame({
        "actual_mw": [100, 200],
        "forecast_mw": [80, 180],
    })

    metrics = calculate_metrics(matched)

    assert metrics["bias_mw"] < 0
