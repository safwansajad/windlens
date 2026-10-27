
import pandas as pd
from analysis import run_analysis

matched, metrics = run_analysis(
    actual_path="data/actual_wind.csv",
    forecast_path="data/wind_forecasts.csv",
    cutoff_hour=9,
    cutoff_minute=50,
)

print("\nACCURACY METRICS")
print(pd.Series(metrics).round(2))

matched.to_csv("matched_forecasts.csv", index=False)

print("\nMatched periods:", len(matched))
print("Saved matched_forecasts.csv")
