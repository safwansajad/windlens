# Wind Forecast Accuracy Dashboard

A full-stack dashboard for exploring day-ahead wind generation forecast accuracy by comparing selected forecasts with observed wind generation.

## Features

- Summary metrics for forecast error
- Interactive chart and forecast-record table
- Search and sorting for forecast records
- FastAPI endpoints for metrics and forecast data
- React frontend served by Nginx
- Docker Compose setup for running the frontend and API together
- Python tests for the analysis logic

## Technology Stack

- **Frontend:** React, Vite, Recharts
- **Backend:** Python, FastAPI
- **Web server / reverse proxy:** Nginx
- **Containerization:** Docker, Docker Compose

## Run with Docker

### Prerequisites

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and make sure Docker is running.

### Start the application

From the repository root, run:

```bash
docker compose up --build -d
```

Open the dashboard:

- <http://localhost:8080>

### API endpoints

- `GET /` - API health check (available directly on the API service at port 8000 inside Docker)
- `GET /api/metrics` - summary forecast-accuracy metrics
- `GET /api/forecasts` - matched hourly forecast and actual records

The frontend's Nginx server proxies `/api/` requests to the FastAPI service, so the metrics and forecast endpoints are available through <http://localhost:8080/api/metrics> and <http://localhost:8080/api/forecasts>.

### Stop the application

```bash
docker compose down
```

## Run the backend locally (optional)

Create and activate a Python virtual environment, install dependencies, and start the API:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The local API runs at <http://127.0.0.1:8000>. For local frontend development, start Vite from `frontend/` in a separate terminal:

```bash
cd frontend
npm ci
npm run dev
```

## Tests

Run the Python analysis tests from the repository root:

```bash
pytest -v
```

Check the frontend build and linting:

```bash
cd frontend
npm run lint
npm run build
```

## Metrics

The dashboard reports forecast error metrics, including:

- **Bias:** mean signed forecast error
- **MAE:** mean absolute error
- **RMSE:** root mean squared error
- **P50 / P90 / P95 absolute error:** percentiles of absolute forecast error

All error values are expressed in MW. The precise interpretation of the metrics depends on the forecast-selection and actual-generation aggregation rules implemented in the analysis code.

## Data and methodology

The application uses the supplied actual-generation and forecast CSV files in `data/`. The analysis code matches hourly actuals with the selected day-ahead forecast for each hour. See `analysis.py` for the implemented selection cutoff, timestamp handling, aggregation, and metric calculations.

## Limitations

- Results depend on the supplied data and the forecast-selection cutoff.
- Hourly aggregation and timestamp conventions affect the comparison.
- Forecast error alone does not establish procurement costs or financial impact.
- Confirm the data source's definitions and the intended operational forecast cutoff before using the results for operational decisions.

## Project structure

```text
.
├── analysis.py
├── main.py
├── data/
├── frontend/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── test_analysis.py
```

## License

No license has been specified yet. Add a license file if you want to explicitly grant others permission to reuse, modify, or distribute this project.
