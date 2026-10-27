
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from analysis import run_analysis

app = FastAPI(
    title="Wind Forecast Accuracy API",
    description="Evaluates day-ahead wind generation forecast accuracy.",
    version="1.0.0",
)

# Allow the local React development server to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Wind Forecast Accuracy API"}


@app.get("/api/metrics")
def get_metrics():
    try:
        _, metrics = run_analysis(
            actual_path="data/actual_wind.csv",
            forecast_path="data/wind_forecasts.csv",
            cutoff_hour=9,
            cutoff_minute=50,
        )
        return metrics
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {exc}",
        ) from exc


@app.get("/api/forecasts")
def get_forecasts():
    try:
        matched, _ = run_analysis(
            actual_path="data/actual_wind.csv",
            forecast_path="data/wind_forecasts.csv",
            cutoff_hour=9,
            cutoff_minute=50,
        )

        # Convert timestamps and NaN values into JSON-safe values.
        matched = matched.astype(object).where(matched.notna(), None)
        records = matched.to_dict(orient="records")

        for record in records:
            for key, value in record.items():
                if hasattr(value, "isoformat"):
                    record[key] = value.isoformat()

        return {"count": len(records), "forecasts": records}
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve forecasts: {exc}",
        ) from exc
