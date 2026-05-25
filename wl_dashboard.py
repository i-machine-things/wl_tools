#!/usr/bin/env python3
"""wl_dashboard.py — HTTP server for WeatherLink Dashboard.

Serves public/ as static files and provides a small read-only API:
  GET /api/current  — fetch live conditions from WeatherLink API v2
  GET /api/history  — return last 7 days of logged data from LOGS/
"""

import glob
import json
import os
import threading
import time as _time
from datetime import datetime, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import requests as _req

BASE_DIR   = Path(__file__).parent
PUBLIC_DIR = BASE_DIR / 'public'
LOGS_DIR   = BASE_DIR / 'LOGS'
PORT       = int(os.environ.get('PORT', 8081))

with open(BASE_DIR / 'config.json') as f:
    _cfg = json.load(f)

_API_KEY    = _cfg['api']['key']
_API_SECRET = _cfg['api']['secret']
_STATION_ID = _cfg['api']['stationId']

_station_name_lock  = threading.Lock()
_station_name_cache = None

def _local_now():
    """Return current time in the configured local timezone, matching wl_logger.py."""
    offset = _cfg.get('timezone', {}).get('offset_hours', 0)
    if _time.localtime().tm_isdst and _time.daylight:
        offset += 1  # DST advances the clock by 1 hour
    return datetime.now() + timedelta(hours=offset)

# Simple 60-second response cache so multiple open tabs don't hammer the API.
_current_lock  = threading.Lock()
_current_cache = None          # (fetched_at: datetime, data: dict)
_CACHE_TTL     = 60            # seconds


def _api_headers():
    return {'x-api-secret': _API_SECRET, 'Content-Type': 'application/json'}


def _station_name():
    global _station_name_cache
    with _station_name_lock:
        if _station_name_cache:
            return _station_name_cache
        try:
            r = _req.get(
                f'https://api.weatherlink.com/v2/stations?api-key={_API_KEY}',
                headers=_api_headers(), timeout=10,
            )
            r.raise_for_status()
            for s in r.json().get('stations', []):
                if str(s.get('station_id')) == str(_STATION_ID):
                    _station_name_cache = s.get('station_name', 'WEATHER STATION').upper()
                    return _station_name_cache
        except Exception:
            pass
        _station_name_cache = 'WEATHER STATION'
        return _station_name_cache


def _fetch_current():
    """Fetch live conditions from WeatherLink API v2, with 60-second cache."""
    global _current_cache
    with _current_lock:
        if _current_cache:
            age = (_local_now() - _current_cache[0]).total_seconds()
            if age < _CACHE_TTL:
                return _current_cache[1]

        try:
            r = _req.get(
                f'https://api.weatherlink.com/v2/current/{_STATION_ID}?api-key={_API_KEY}',
                headers=_api_headers(), timeout=10,
            )
            r.raise_for_status()
            raw = r.json()
        except Exception as e:
            print(f'[wl_dashboard] _fetch_current error: {e}', flush=True)
            return {'error': 'Failed to fetch current conditions from WeatherLink'}

        data = None
        if 'sensors' in raw:
            for sensor in raw.get('sensors', []):
                if sensor.get('data'):
                    sd = sensor['data'][0]
                    if 'temp' in sd and 'hum' in sd:
                        data = sd
                        break
        elif 'data' in raw:
            arr = raw.get('data', [])
            data = arr[0] if arr else None

        if not data:
            return {'error': 'No sensor data in API response'}

        result = {
            '_station_name': _station_name(),
            'timestamp':     _local_now().isoformat(),
            'temp':          data.get('temp'),
            'humidity':      data.get('hum'),
            'dew_point':     data.get('dew_point'),
            'heat_index':    data.get('heat_index'),
            'wet_bulb':      data.get('wet_bulb'),
            'pm_1':          data.get('pm_1'),
            'pm_2p5':        data.get('pm_2p5'),
            'pm_10':         data.get('pm_10'),
            'aqi_val':       data.get('aqi_val'),
            'aqi_desc':      data.get('aqi_desc'),
            'wind_speed':    data.get('wind_speed_last'),
            'wind_gust':     data.get('wind_speed_hi_last_2_min'),
            'wind_dir':      data.get('wind_dir_scalar_avg_last_2_min'),
            'pressure':      data.get('bar_sea_level'),
            'rainfall':      data.get('rain_day_in'),
            'solar_rad':     data.get('solar_rad'),
            'uv_index':      data.get('uv_index'),
            'temp_in':       data.get('temp_in'),
            'hum_in':        data.get('hum_in'),
        }
        _current_cache = (_local_now(), result)
        return result


def _fetch_history(days=7):
    """Return up to 600 records from the last `days` days of LOGS/*.json files."""
    if not LOGS_DIR.exists():
        return []
    cutoff  = _local_now() - timedelta(days=days)
    records = []
    def _file_date(p):
        try: return datetime.strptime(p.stem[len('weather_data_'):], '%b_%Y')
        except ValueError: return datetime.min
    for fp in sorted(LOGS_DIR.glob('weather_data_*.json'), key=_file_date)[-3:]:
        try:
            records.extend(json.loads(fp.read_text()))
        except Exception:
            pass
    out = []
    for r in records:
        try:
            if datetime.fromisoformat(r.get('timestamp', '')) >= cutoff:
                out.append(r)
        except Exception:
            continue
    return out[-600:]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    # ── Routing ───────────────────────────────────────────────────────────────

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/current':
            self._get_current()
        elif path == '/api/history':
            self._get_history()
        else:
            super().do_GET()

    # ── Handlers ─────────────────────────────────────────────────────────────

    def _get_current(self):
        data = _fetch_current()
        self._json(502 if 'error' in data else 200, data)

    def _get_history(self):
        self._json(200, _fetch_history())

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f'[{self.log_date_time_string()}] {fmt % args}', flush=True)


if __name__ == '__main__':
    PUBLIC_DIR.mkdir(exist_ok=True)
    httpd = ThreadingHTTPServer(('', PORT), Handler)
    print(f'WeatherLink Dashboard on :{PORT}  (public/ → /)', flush=True)
    httpd.serve_forever()
