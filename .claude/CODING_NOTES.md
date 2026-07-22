# Coding Notes — wl_tools

## Dashboard architecture

`public/index.html` is a single-file SPA. All CSS, JS, and HTML are inline — no build step, no bundler. This is intentional: the file is served directly by Python's `SimpleHTTPRequestHandler` with zero dependencies beyond Chart.js (CDN).

Keep it that way. Do not introduce a framework, module bundler, or separate CSS file without a strong reason.

## Config pattern

`config.json` is never committed. `example.config.json` is the committed template. If a new config key is added, update `example.config.json` at the same time.

## API caching

`wl_dashboard.py` caches the WeatherLink API response for 60 seconds to avoid rate-limiting. The cache is in-memory (lost on restart). Do not reduce the cache TTL below 60 s.

## Data files

`LOGS/` files are named `weather_data_MMM_YYYY.{csv,json}`. The dashboard reads the last 7 days from JSON. The CSV is for Excel/offline use only — the dashboard never reads it.

## Widget system

Each dashboard card has a `data-wid` attribute (e.g. `w-temp`, `w-forecast`). Widget visibility and order are persisted in `localStorage`. When adding a new card:
1. Give it a unique `data-wid`
2. Add an entry to `WIDGET_NAMES` in `index.html`
3. Ensure it appears in a `<div class="dash-row">` so the edit/drag system picks it up

## 5-day forecast

Uses the Open-Meteo API (free, no key). Requires browser geolocation permission. Responses are cached in `_fcCache` for 30 minutes to avoid re-fetching on every 5-minute dashboard refresh.
