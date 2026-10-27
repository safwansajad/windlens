
import pandas as pd
import numpy as np

UK_TZ = "Europe/London"


def load_data(actual_path, forecast_path):
    """Load and clean the actual and forecast datasets."""
    actuals = pd.read_csv(actual_path)
    forecasts = pd.read_csv(forecast_path)

    actuals["startTime"] = pd.to_datetime(
        actuals["startTime"], utc=True, errors="coerce"
    )
    forecasts["startTime"] = pd.to_datetime(
        forecasts["startTime"], utc=True, errors="coerce"
    )
    forecasts["publishTime"] = pd.to_datetime(
        forecasts["publishTime"], utc=True, errors="coerce"
    )

    actuals["generation"] = pd.to_numeric(
        actuals["generation"], errors="coerce"
    )
    forecasts["generation"] = pd.to_numeric(
        forecasts["generation"], errors="coerce"
    )

    actuals = actuals.dropna(
        subset=["startTime", "generation"]
    )
    forecasts = forecasts.dropna(
        subset=["startTime", "publishTime", "generation"]
    )

    actuals = actuals[
        actuals["fuelType"].str.upper() == "WIND"
    ].copy()

    return actuals, forecasts


def build_hourly_actuals(actuals):
    """Aggregate two complete half-hour records into hourly averages."""
    actuals = actuals.copy()
    actuals["hour_start"] = actuals["startTime"].dt.floor("h")

    hourly = (
        actuals.groupby("hour_start")
        .agg(
            actual_mw=("generation", "mean"),
            half_hour_count=("generation", "count"),
        )
        .reset_index()
    )

    return hourly[hourly["half_hour_count"] == 2].copy()


def select_forecasts(forecasts, cutoff_hour=9, cutoff_minute=50):
    """Select the latest forecast published before each D-1 cutoff."""
    forecasts = forecasts.copy()

    forecasts["delivery_local"] = (
        forecasts["startTime"].dt.tz_convert(UK_TZ).dt.date
    )

    forecasts["decision_date"] = (
        pd.to_datetime(forecasts["delivery_local"])
        - pd.Timedelta(days=1)
    ).dt.date

    start_date = pd.Timestamp("2026-01-01").date()
    end_date = pd.Timestamp("2026-02-01").date()

    forecasts = forecasts[
        (forecasts["decision_date"] >= start_date)
        & (forecasts["decision_date"] < end_date)
    ].copy()

    def make_cutoff(decision_date):
        local = pd.Timestamp(
            f"{decision_date} {cutoff_hour:02d}:{cutoff_minute:02d}",
            tz=UK_TZ,
        )
        return local.tz_convert("UTC")

    forecasts["cutoff_utc"] = forecasts["decision_date"].apply(
        make_cutoff
    )

    eligible = forecasts[
        forecasts["publishTime"] <= forecasts["cutoff_utc"]
    ].copy()

    if eligible.duplicated(["startTime", "publishTime"]).any():
        raise ValueError(
            "Duplicate target/publication records require investigation."
        )

    selected = (
        eligible.sort_values("publishTime")
        .drop_duplicates("startTime", keep="last")
        [["startTime", "publishTime", "generation"]]
        .rename(columns={
            "publishTime": "forecast_published_at",
            "generation": "forecast_mw",
        })
    )

    return selected


def calculate_metrics(matched):
    """Calculate standard forecast error metrics."""
    errors = matched["forecast_mw"] - matched["actual_mw"]
    absolute_errors = errors.abs()

    return {
        "matched_hours": int(len(matched)),
        "bias_mw": float(errors.mean()),
        "mae_mw": float(absolute_errors.mean()),
        "rmse_mw": float(np.sqrt((errors ** 2).mean())),
        "p50_absolute_error_mw": float(
            absolute_errors.quantile(0.50)
        ),
        "p90_absolute_error_mw": float(
            absolute_errors.quantile(0.90)
        ),
        "p95_absolute_error_mw": float(
            absolute_errors.quantile(0.95)
        ),
    }


def run_analysis(
    actual_path="data/actual_wind.csv",
    forecast_path="data/wind_forecasts.csv",
    cutoff_hour=9,
    cutoff_minute=50,
):
    actuals, forecasts = load_data(actual_path, forecast_path)

    hourly_actuals = build_hourly_actuals(actuals)

    selected = select_forecasts(
        forecasts,
        cutoff_hour=cutoff_hour,
        cutoff_minute=cutoff_minute,
    )

    matched = hourly_actuals.merge(
        selected,
        left_on="hour_start",
        right_on="startTime",
        how="inner",
        validate="one_to_one",
    )

    if matched.empty:
        raise ValueError("No matching actual and forecast records.")

    matched["error_mw"] = (
        matched["forecast_mw"] - matched["actual_mw"]
    )
    matched["absolute_error_mw"] = matched["error_mw"].abs()

    metrics = calculate_metrics(matched)

    return matched, metrics
