
import requests
import pandas as pd

url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream"

params = {
    "publishDateTimeFrom": "2026-01-01T00:00:00Z",
    "publishDateTimeTo": "2026-02-01T00:00:00Z",
    "settlementDateFrom": "2026-01-01",
    "settlementDateTo": "2026-02-02",
}

response = requests.get(url, params=params, timeout=60)

print("Status code:", response.status_code)
response.raise_for_status()

data = response.json()

print("Number of records:", len(data))
print("First record:", data[0] if data else "No records")

df = pd.DataFrame(data)
print(df.head())
print(df.columns.tolist())

df.to_csv("wind_forecasts.csv", index=False)