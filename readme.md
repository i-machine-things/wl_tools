# wl_tools — WeatherLink Dashboard & Logger

A Python suite that polls the Davis WeatherLink API v2, logs readings to CSV/JSON, and serves a real-time environmental dashboard in the browser.

![CI](https://github.com/i-machine-things/wl_tools/actions/workflows/ci.yml/badge.svg)

## Features

- **Live dashboard** — dark/light theme, auto-refreshes every 5 minutes, shows sample data instantly before the API responds
- **4-column responsive grid** — drag widgets to reorder, drag their right edge to resize (1–4 columns), hide/show per widget, all persisted to `localStorage`
- **5-day forecast** — Open-Meteo (no API key), uses config lat/lon, browser geolocation, or a city/ZIP you type in edit mode; each day shows high/low, precipitation chance, and dominant wind direction
- **Data logging** — CSV + JSON per month, stored in `LOGS/`
- **Daily email report** — sends a summary and CSV attachment via SMTP/Gmail
- **CI** — flake8 lint + bandit security scan on every push

## Requirements

- Python 3.7+
- `requests` (`pip install -r requirements.txt`)
- A Davis WeatherLink account with API v2 credentials

## Installation

```bash
git clone https://github.com/i-machine-things/wl_tools.git
cd wl_tools
pip install -r requirements.txt
cp example.config.json config.json
```

Edit `config.json`:

```json
{
    "api": {
        "key":       "YOUR_API_KEY",
        "secret":    "YOUR_API_SECRET",
        "stationId": "YOUR_STATION_ID"
    },
    "email": {
        "sender_email":    "you@gmail.com",
        "sender_password": "app-specific-password",
        "recipient_email": ["you@gmail.com"],
        "smtp_server":     "smtp.gmail.com",
        "smtp_port":       587
    },
    "timezone": {
        "offset_hours": -8
    },
    "location": {
        "lat": 47.6062,
        "lon": -122.3321
    }
}
```

> **`location`** is optional but improves the 5-day forecast on first load. If omitted the forecast falls back to browser geolocation or a city search in edit mode.

Get your API credentials from [weatherlink.com/account/api](https://weatherlink.com/account/api).  
Find your station ID by running `python wl_logger.py --list-stations`.

## Dashboard

```bash
python wl_dashboard.py
```

Open **http://localhost:8081**. The dashboard shows built-in sample data immediately and replaces it silently when the API responds. A `SAMPLE DATA` badge in the header disappears once live data loads; it switches to `NO CONNECTION` if the API is unreachable.

### Edit mode

Click **EDIT** in the header to enter edit mode:

| Action | Result |
|---|---|
| Click a widget overlay | Toggle visibility |
| Drag the grip (≡) | Reorder widgets |
| Drag the blue handle on the right edge | Resize (1–4 columns) |
| Click the column indicator (■□□□) | Cycle column width |
| Set a location in the forecast widget | Save city/ZIP for the forecast |

All layout changes persist across page reloads via `localStorage`.

## Logger

Poll the API once and write to `LOGS/`:

```bash
python wl_logger.py
```

Schedule with crontab (Linux/macOS) or Task Scheduler (Windows):

```bash
# Every 15 minutes
*/15 * * * * /usr/bin/python3 /path/to/wl_logger.py
```

Logs are written to `LOGS/weather_data_<Mon>_<YYYY>.csv` and `.json`.

### Logged fields

| Field | Description |
|---|---|
| `timestamp` | ISO 8601 local time |
| `temp` | Temperature (°F) |
| `humidity` | Relative humidity (%) |
| `dew_point` | Dew point (°F) |
| `heat_index` | Apparent temperature (°F) |
| `wet_bulb` | Wet bulb temperature (°F) |
| `pm_1` / `pm_2p5` / `pm_10` | Particulate matter (µg/m³) |
| `aqi_val` / `aqi_desc` | US EPA AQI value and category |
| `wind_speed` / `wind_gust` | MPH |
| `wind_dir` | Degrees |
| `pressure` | Barometric pressure (inHg) |
| `rainfall` | Daily accumulation (in) |
| `solar_rad` | Solar radiation (W/m²) |
| `uv_index` | UV index |

## Email report

```bash
python wl_report.py
```

Schedule a daily summary:

```bash
# Daily at 8 PM
0 20 * * * /usr/bin/python3 /path/to/wl_report.py
```

Requires Gmail app-specific password — see [Google's guide](https://support.google.com/accounts/answer/185833).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `SAMPLE DATA` badge stays visible | `config.json` not found or API credentials invalid — check key/secret/stationId |
| `NO CONNECTION` badge | Dashboard server running but API unreachable — verify credentials and network |
| `401 Unauthorized` | Wrong API key or secret |
| Forecast not loading | Set `location.lat`/`lon` in `config.json`, or use edit mode to search by city |
| Crontab not running | Check full Python path (`which python3`) and script path (`pwd`) |

## License

GNU General Public License — see [LICENSE](LICENSE) for details.
