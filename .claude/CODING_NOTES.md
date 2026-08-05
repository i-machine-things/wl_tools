# Coding Notes — wl_tools

> **Style rule:** Notes must be clear and concise — 300 characters or less each. Group by topic, not by date. Whenever a PR review (CodeRabbit or human) catches a mistake, add or amend a note here right away so it isn't repeated.

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

**Resolve widget spans via `_resolveSpan(wid)`, never `wSpans[wid] || 1`.** Only the helper honors `DEFAULT_SPANS` (e.g. `w-forecast` = 4); use it in `applyWidgetSpans`, `cycleWidgetSpan`, resize `curSpan` init, and span indicators, or defaults get lost.

**Derive resize column count from the grid, not a hardcoded literal.** `startCardResize` should read `getComputedStyle(row).gridTemplateColumns.split(' ').length` at drag start — responsive breakpoints use 2 or 1 columns, so a fixed `cols = 4` breaks resize math.

## 5-day forecast

Uses the Open-Meteo API (free, no key). Requires browser geolocation permission. Responses are cached in `_fcCache` for 30 minutes to avoid re-fetching on every 5-minute dashboard refresh.

**Mock mode must still update UI state.** When `fetchForecast` short-circuits to `MOCK_FORECAST`, call `_updateFcSubtitle('Sample Data')` first, or `#fc-subtitle` stays stuck on "Loading…".

**Use Open-Meteo's underscored daily field names** (`wind_direction_10m_dominant`, `wind_speed_10m_max`), not the legacy unspaced form (`winddirection_10m_dominant`, `windspeed_10m_max`). Both work today, but underscored is the documented current API — CodeRabbit PR #12 flagged the legacy form.

## Security (XSS)

**Never interpolate untrusted strings into `innerHTML`.** Geolocation labels (Nominatim `display_name`) and API `err.message` can contain `<`/`>`; leave the target element empty in the template and set text via `.textContent` instead.
