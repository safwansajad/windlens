
import pandas as pd

df = pd.read_csv("matched_forecasts.csv")

for col in ["startTime", "forecast_published_at"]:
    df[col] = pd.to_datetime(df[col], utc=True)

# Check the coverage of the matched dataset.
print("Delivery start:", df["startTime"].min())
print("Delivery end:", df["startTime"].max())
print("Unique delivery hours:", df["startTime"].nunique())
print("Duplicate delivery hours:", df["startTime"].duplicated().sum())

# Inspect the first and last few matched records.
print("\nFIRST 5 MATCHED RECORDS")
print(df.head().to_string(index=False))

print("\nLAST 5 MATCHED RECORDS")
print(df.tail().to_string(index=False))

# Calculate forecast horizon using the actual cutoff
# assumed by the analysis: 10:00 UK time on the prior day.
uk_delivery = df["startTime"].dt.tz_convert("Europe/London")

cutoff_local = (
    uk_delivery.dt.normalize()
    - pd.Timedelta(days=1)
    + pd.Timedelta(hours=10)
)

cutoff_utc = cutoff_local.dt.tz_convert("UTC")

df["forecast_lead_hours"] = (
    df["startTime"] - df["forecast_published_at"]
).dt.total_seconds() / 3600

print("\nCUTOFF VALIDATION")
print(
    "Forecasts published after cutoff:",
    (df["forecast_published_at"] > cutoff_utc).sum()
)

print("\nFORECAST LEAD TIME IN HOURS")
print(df["forecast_lead_hours"].describe().round(2))

print("\nERROR SUMMARY")
print(
    df[["actual_mw", "forecast_mw", "error_mw"]]
    .describe()
    .round(2)
)
