
import pandas as pd
import numpy as np

DATA_DIR = "data"

# Provisional assumption only.
# Verify the applicable market deadline before finalising.
CUTOFF_HOUR = 10
CUTOFF_MINUTE = 0
UK_TZ = "Europe/London"

actuals = pd.read_csv(f"{DATA_DIR}/actual_wind.csv")
forecasts = pd.read_csv(f"{DATA_DIR}/wind_forecasts.csv")

# Parse timestamps in UTC.
for col in ["startTime"]:
    actuals[col] = pd.to_datetime(
        actuals[col], utc=True, errors="coerce"
    )

for col in ["startTime", "publishTime"]:
    forecasts[col] = pd.to_datetime(
        forecasts[col], utc=True, errors="coerce"
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

# Keep actual wind generation only.
actuals = actuals[
    actuals["fuelType"].str.upper() == "WIND"
].copy()

# STEP 1: Aggregate half-hourly actuals into hourly averages.
actuals["hour_start"] = actuals["startTime"].dt.floor("h")

hourly_actuals = (
    actuals.groupby("hour_start")
    .agg(
        actual_mw=("generation", "mean"),
        half_hour_count=("generation", "count"),
    )
    .reset_index()
)

# Require both half-hour periods for a complete hour.
hourly_actuals = hourly_actuals[
    hourly_actuals["half_hour_count"] == 2
].copy()

# STEP 2: Derive delivery date and previous-day decision date.
forecasts["delivery_local"] = (
    forecasts["startTime"]
    .dt.tz_convert(UK_TZ)
    .dt.date
)

forecasts["decision_date"] = (
    pd.to_datetime(forecasts["delivery_local"])
    - pd.Timedelta(days=1)
).dt.date

# January 2026 decision dates mean delivery dates
# from Jan 2 through Feb 1, inclusive.
decision_start = pd.Timestamp("2026-01-01").date()
decision_end = pd.Timestamp("2026-02-01").date()

forecasts = forecasts[
    (forecasts["decision_date"] >= decision_start)
    & (forecasts["decision_date"] < decision_end)
].copy()

# STEP 3: Calculate a separate UK-local cutoff per target.
def make_cutoff(decision_date):
    cutoff_local = pd.Timestamp(
        f"{decision_date} "
        f"{CUTOFF_HOUR:02d}:{CUTOFF_MINUTE:02d}",
        tz=UK_TZ,
    )
    return cutoff_local.tz_convert("UTC")

forecasts["cutoff_utc"] = forecasts[
    "decision_date"
].apply(make_cutoff)

# STEP 4: Retain only forecasts published by the cutoff.
eligible = forecasts[
    forecasts["publishTime"] <= forecasts["cutoff_utc"]
].copy()

# Check for ambiguous duplicate versions.
duplicate_versions = eligible.duplicated(
    subset=["startTime", "publishTime"], keep=False
)

if duplicate_versions.any():
    raise ValueError(
        "Duplicate records for the same target and publication "
        "time found. Investigate before selecting forecasts."
    )

# Select the latest eligible forecast for each target hour.
selected = (
    eligible.sort_values("publishTime")
    .drop_duplicates(subset=["startTime"], keep="last")
    [["startTime", "publishTime", "generation"]]
    .rename(columns={
        "generation": "forecast_mw",
        "publishTime": "forecast_published_at",
    })
)

# STEP 5: Join hourly forecasts to hourly actuals.
matched = hourly_actuals.merge(
    selected,
    left_on="hour_start",
    right_on="startTime",
    how="inner",
    validate="one_to_one",
)

# STEP 6: Calculate errors.
matched["error_mw"] = (
    matched["forecast_mw"] - matched["actual_mw"]
)
matched["absolute_error_mw"] = matched["error_mw"].abs()

if matched.empty:
    raise ValueError(
        "No matching records. Check date coverage, timestamps "
        "and the cutoff assumption."
    )

metrics = {
    "matched_hours": len(matched),
    "bias_mw": matched["error_mw"].mean(),
    "mae_mw": matched["absolute_error_mw"].mean(),
    "rmse_mw": np.sqrt((matched["error_mw"] ** 2).mean()),
    "p50_absolute_error_mw": matched["absolute_error_mw"].quantile(0.50),
    "p90_absolute_error_mw": matched["absolute_error_mw"].quantile(0.90),
    "p95_absolute_error_mw": matched["absolute_error_mw"].quantile(0.95),
}

print("\nMATCHING SUMMARY")
print("Hourly actuals:", len(hourly_actuals))
print("Eligible forecasts:", len(eligible))
print("Selected forecasts:", len(selected))
print("Matched hours:", len(matched))

print("\nACCURACY METRICS")
print(pd.Series(metrics).round(2))

matched.to_csv("matched_forecasts.csv", index=False)
print("\nSaved matched_forecasts.csv")
