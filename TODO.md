# SmartCity Pulse - TODO

**Goal**: Build a full time-series data pipeline with live Grafana dashboards in one afternoon, showcasing GitHub Copilot.

---

## Phase 1: Project Scaffolding

- [x] Create `.gitignore` (Python venv, `__pycache__`, `.env`, IDE files)
- [x] Create `.env.example` with placeholder config:
  ```
  INFLUXDB_TOKEN=changeme
  INFLUXDB_ORG=smartcity
  INFLUXDB_BUCKET=sensors
  INFLUXDB_URL=http://localhost:8086
  GRAFANA_ADMIN_PASSWORD=admin
  ```
- [x] Create `requirements.txt` (`influxdb-client`, `python-dotenv`)
- [x] Create `config.py` (reads `.env`, exports settings)

### Docker Environment
- [x] Create `docker-compose.yml`:
  - InfluxDB 2 (port 8086, auto-setup with env vars)
  - Grafana (port 3000, provisioning volume mounts)
- [x] Create `provisioning/datasources/influxdb.yml` (auto-configures Grafana → InfluxDB)
- [x] Create `provisioning/dashboards/dashboard.yml` (points to JSON dashboard file)
- [x] `docker compose up -d` — verify:
  - InfluxDB at http://localhost:8086
  - Grafana at http://localhost:3000 (datasource pre-configured)

---

## Phase 2: Data Ingestion

- [x] Create `ingest_smartcity.py`:
  - 10 sensor stations across 4 zones (center, industrial, residential, park)
  - Measurements: `air_quality`, `traffic`, `weather`
  - Realistic patterns: rush-hour spikes (7-9am, 5-7pm), diurnal temperature, zone-based baselines
  - Writes batches every 10 seconds
- [x] Run ingestion: `python ingest_smartcity.py`
- [x] Verify data in InfluxDB Data Explorer

### Data Quality Checks
- [x] Confirm correct tags (station, zone) and fields appear
- [x] Confirm timestamps are reasonable
- [x] Let it run 2-3 minutes to accumulate enough data for dashboards

---

## Phase 3: Grafana Dashboards (The Star of the Show)

### Dashboard Setup
- [x] Create dashboard: "SmartCity Pulse - Urban Monitoring"
- [x] Add template variables: `$station` (query), `$zone` (multi-value)

### Panels to Build

| # | Panel | Type | Key Flux Feature |
|---|-------|------|------------------|
| 1 | Current AQI | Gauge | `last()` + color thresholds |
| 2 | PM2.5 / PM10 / NO₂ Trends | Time series | Basic range query |
| 3 | 5-Minute Averages | Time series | `aggregateWindow(every: 5m, fn: mean)` |
| 4 | Traffic vs Pollution | Dual-axis | `join()` or `union()` |
| 5 | Zone Comparison | Bar chart | `group(columns: ["zone"])` |
| 6 | Station Map | Geomap | Hardcoded lat/lon + AQI color |
| 7 | Moving Average + Anomalies | Time series | `movingAverage()` + `timedMovingAverage()` |
| 8 | Pollution Spike Alert | Alert list | Grafana alert rule (PM2.5 > 50) |

### Advanced InfluxDB Features
- [x] Create InfluxDB **Task**: hourly downsampling to `sensors_downsampled` bucket
- [x] Add Grafana **annotations** for rush-hour windows
- [x] Configure at least one **alert rule** (PM2.5 threshold breach)

### Flux Queries to Implement (Copilot-assisted)
- [ ] Custom AQI calculation using `map()`:
  ```flux
  |> map(fn: (r) => ({ r with aqi_category:
      if r.pm25 <= 12.0 then "Good"
      else if r.pm25 <= 35.4 then "Moderate"
      else if r.pm25 <= 55.4 then "Unhealthy (Sensitive)"
      else "Unhealthy"
  }))
  ```
- [ ] `pivot()` for wide-format table panels
- [ ] Time-shift comparison (today vs yesterday)

---

## Phase 4: Polish & Export

- [x] Export final dashboard as JSON → `provisioning/dashboards/smartcity-pulse.json`
- [x] Verify full cycle: `docker compose down -v && docker compose up -d` → dashboards appear
- [x] Take screenshots → `docs/dashboard-preview.png`
- [x] Update README with actual screenshot
- [x] Add auto-refresh (10s) and time range (Last 30 minutes) as dashboard defaults
- [ ] Final commit with clean history

---

## Stretch Goals (If Time Permits)

- [ ] Add more sensor types (noise levels, EV charging utilization)
- [ ] Replay a historical CSV dataset instead of live simulation
- [ ] Grafana playlist mode for kiosk/demo display
- [ ] Performance test: crank up to 100 stations, measure write throughput

---

## Success Criteria

- [ ] `git clone` → `docker compose up` → `python ingest_smartcity.py` → live dashboards in < 5 min
- [ ] At least 6 distinct dashboard panels with different visualization types
- [ ] At least 3 advanced Flux features demonstrated (aggregateWindow, map, movingAverage, join, pivot)
- [ ] Dashboard is fully provisioned (no manual Grafana clicks needed to reproduce)
- [ ] Code is clean, type-hinted, and demonstrates clear Copilot collaboration