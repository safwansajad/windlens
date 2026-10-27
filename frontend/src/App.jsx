
import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity, AlertTriangle, Clock3, Search } from "lucide-react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "";
const formatMW = (value) =>
  `${Number(value).toLocaleString("en-GB", {
    maximumFractionDigits: 1,
  })} MW`;

const formatNumber = (value) =>
  Number(value).toLocaleString("en-GB", {
    maximumFractionDigits: 1,
  });

const formatDate = (value) =>
  new Date(value).toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    timeZone: "Europe/London",
  });

function App() {
  const [metrics, setMetrics] = useState(null);
  const [forecasts, setForecasts] = useState([]);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("hour_start");
  const [sortDirection, setSortDirection] = useState("asc");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [metricsResponse, forecastsResponse] = await Promise.all([
          fetch(`${API_URL}/api/metrics`),
          fetch(`${API_URL}/api/forecasts`),
        ]);

        if (!metricsResponse.ok || !forecastsResponse.ok) {
          throw new Error(
            "The API returned an error. Check that FastAPI is running."
          );
        }

        const metricsData = await metricsResponse.json();
        const forecastsData = await forecastsResponse.json();

        setMetrics(metricsData);
        setForecasts(forecastsData.forecasts ?? []);
      } catch (err) {
        setError(err.message || "Unable to load dashboard data.");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  const chartData = useMemo(
    () =>
      [...forecasts]
        .sort(
          (a, b) =>
            new Date(a.hour_start).getTime() -
            new Date(b.hour_start).getTime()
        )
        .map((item) => ({
          ...item,
          chartTime: formatDate(item.hour_start),
        })),
    [forecasts]
  );

  const filteredForecasts = useMemo(() => {
    const query = search.trim().toLowerCase();

    return forecasts
      .filter((item) => {
        if (!query) return true;

        return (
          formatDate(item.hour_start).toLowerCase().includes(query) ||
          String(item.actual_mw).includes(query) ||
          String(item.forecast_mw).includes(query) ||
          String(item.error_mw).includes(query) ||
          String(item.absolute_error_mw).includes(query)
        );
      })
      .sort((a, b) => {
        let comparison;

        if (sortBy === "hour_start") {
          comparison =
            new Date(a.hour_start).getTime() -
            new Date(b.hour_start).getTime();
        } else {
          comparison = Number(a[sortBy]) - Number(b[sortBy]);
        }

        if (comparison === 0) {
          comparison =
            new Date(a.hour_start).getTime() -
            new Date(b.hour_start).getTime();
        }

        return sortDirection === "asc" ? comparison : -comparison;
      });
  }, [forecasts, search, sortBy, sortDirection]);

  function handleSortChange(event) {
    setSortBy(event.target.value);
    setSortDirection(
      event.target.value === "hour_start" ? "asc" : "desc"
    );
  }

  if (loading) {
    return (
      <main className="status-screen">
        <Activity size={28} />
        <p>Loading wind forecast analysis...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="status-screen">
        <AlertTriangle size={28} />
        <h2>Could not load dashboard</h2>
        <p>{error}</p>
        <p>Check that FastAPI is running on port 8000.</p>
      </main>
    );
  }

  if (!metrics) {
    return (
      <main className="status-screen">
        <h2>No metrics available</h2>
      </main>
    );
  }

  return (
    <main className="dashboard">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">
            <Activity size={23} />
          </div>
          <div>
            <h1>WindLens</h1>
            <p>Forecast intelligence</p>
          </div>
        </div>

        <span className="live-status">
          <span className="status-dot" />
          API connected
        </span>
      </header>

      <section className="page-heading">
        <div>
          <p className="eyebrow">ENERGY MARKET ANALYTICS</p>
          <h2>Wind forecast accuracy</h2>
          <p className="subtitle">
            Evaluate day-ahead wind forecasts against actual generation.
          </p>
        </div>

        <div className="period-chip">
          <Clock3 size={16} />
          January 2026
        </div>
      </section>

      <section className="metric-grid">
        <MetricCard
          label="Mean absolute error"
          value={formatMW(metrics.mae_mw)}
          note="Average absolute difference"
          accent="blue"
        />

        <MetricCard
          label="Root mean squared error"
          value={formatMW(metrics.rmse_mw)}
          note="Penalizes larger errors"
          accent="purple"
        />

        <MetricCard
          label="Forecast bias"
          value={`${metrics.bias_mw > 0 ? "+" : ""}${formatMW(
            metrics.bias_mw
          )}`}
          note={
            metrics.bias_mw > 0
              ? "Overestimated on average"
              : metrics.bias_mw < 0
                ? "Underestimated on average"
                : "No average bias"
          }
          accent="orange"
        />

        <MetricCard
          label="Matched delivery hours"
          value={formatNumber(metrics.matched_hours)}
          note="Forecast and actual available"
          accent="green"
        />
      </section>

      <section className="panel chart-panel">
        <div className="panel-heading">
          <div>
            <h3>Actual vs. forecast generation</h3>
            <p>Hourly wind generation, measured in megawatts (MW)</p>
          </div>

          <span className="chart-period">2 Jan – 1 Feb 2026</span>
        </div>

        <div className="chart-legend">
          <span>
            <i className="legend-dot actual-dot" />
            Actual generation
          </span>
          <span>
            <i className="legend-dot forecast-dot" />
            Day-ahead forecast
          </span>
        </div>

        <div className="chart-container">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 12, right: 16, left: 8, bottom: 8 }}
            >
              <CartesianGrid stroke="#e9edf3" strokeDasharray="4 4" />

              <XAxis
                dataKey="hour_start"
                type="category"
                tickFormatter={(value) =>
                  new Date(value).toLocaleDateString("en-GB", {
                    day: "2-digit",
                    month: "short",
                    timeZone: "Europe/London",
                  })
                }
                interval={71}
                tick={{ fontSize: 11, fill: "#68758a" }}
                tickLine={false}
                axisLine={false}
              />

              <YAxis
                tickFormatter={(value) => `${Math.round(value / 1000)}k`}
                tick={{ fontSize: 11, fill: "#68758a" }}
                tickLine={false}
                axisLine={false}
                width={44}
              />

              <Tooltip
                labelFormatter={(value) => formatDate(value)}
                formatter={(value, name) => [
                  formatMW(value),
                  name === "actual_mw" ? "Actual" : "Forecast",
                ]}
                contentStyle={{
                  borderRadius: 10,
                  border: "1px solid #e1e6ee",
                  fontSize: 12,
                }}
              />

              <Legend
                formatter={(value) =>
                  value === "actual_mw" ? "Actual" : "Forecast"
                }
              />

              <Line
                type="monotone"
                dataKey="actual_mw"
                name="actual_mw"
                stroke="#2878d0"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
                isAnimationActive={false}
              />

              <Line
                type="monotone"
                dataKey="forecast_mw"
                name="forecast_mw"
                stroke="#e99a3b"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel table-panel">
        <div className="panel-heading table-heading">
          <div>
            <h3>Delivery period analysis</h3>
            <p>
              Search delivery hours and compare forecast values with actual
              generation.
            </p>
          </div>

          <div className="sort-controls">
            <label htmlFor="sortBy">Sort by</label>

            <select
              id="sortBy"
              value={sortBy}
              onChange={handleSortChange}
            >
              <option value="hour_start">Delivery time</option>
              <option value="absolute_error_mw">Absolute error</option>
              <option value="error_mw">Signed error</option>
              <option value="actual_mw">Actual generation</option>
              <option value="forecast_mw">Forecast generation</option>
            </select>

            <button
              type="button"
              className="sort-button"
              onClick={() =>
                setSortDirection((direction) =>
                  direction === "asc" ? "desc" : "asc"
                )
              }
            >
              {sortDirection === "asc"
                ? "Ascending ↑"
                : "Descending ↓"}
            </button>
          </div>
        </div>

        <label className="search-box">
          <Search size={18} />

          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search date, actual, forecast or error..."
            aria-label="Search delivery hours"
          />

          {search && (
            <button
              type="button"
              className="clear-search"
              onClick={() => setSearch("")}
              aria-label="Clear search"
            >
              ×
            </button>
          )}
        </label>

        <p className="result-count">
          Showing {Math.min(filteredForecasts.length, 100)} of{" "}
          {filteredForecasts.length} matching delivery hours
        </p>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Delivery time (UK)</th>
                <th>Actual (MW)</th>
                <th>Forecast (MW)</th>
                <th>Signed error (MW)</th>
                <th>Absolute error (MW)</th>
              </tr>
            </thead>

            <tbody>
              {filteredForecasts.slice(0, 100).map((item) => (
                <tr key={item.hour_start}>
                  <td>{formatDate(item.hour_start)}</td>
                  <td>{formatNumber(item.actual_mw)}</td>
                  <td>{formatNumber(item.forecast_mw)}</td>

                  <td>
                    <span
                      className={
                        item.error_mw > 0
                          ? "error-positive"
                          : item.error_mw < 0
                            ? "error-negative"
                            : ""
                      }
                    >
                      {item.error_mw > 0 ? "+" : ""}
                      {formatNumber(item.error_mw)}
                    </span>
                  </td>

                  <td className="absolute-error">
                    {formatNumber(item.absolute_error_mw)}
                  </td>
                </tr>
              ))}

              {filteredForecasts.length === 0 && (
                <tr>
                  <td colSpan={5} className="empty-state">
                    No delivery periods match your search.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {filteredForecasts.length > 100 && (
          <p className="table-note">
            Showing the first 100 matching rows. Use search and sorting to
            locate specific delivery periods.
          </p>
        )}
      </section>

      <footer className="footer">
        <p>
          Decision cutoff: 09:50 UK time on the day before delivery, as
          currently configured. Verify this assumption against the relevant
          market rules.
        </p>
        <p>Source: Elexon wind generation actuals and forecasts.</p>
      </footer>
    </main>
  );
}

function MetricCard({ label, value, note, accent }) {
  return (
    <article className="metric-card">
      <div className={`metric-accent ${accent}`} />
      <p className="metric-label">{label}</p>
      <h3>{value}</h3>
      <p className="metric-note">{note}</p>
    </article>
  );
}

export default App;
