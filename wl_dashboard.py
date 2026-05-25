#!/usr/bin/env python3
"""
Weather Station Dashboard Server
Run:  python3 wl_dashboard.py
Open: http://localhost:8081
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import glob
import requests
from datetime import datetime, timedelta
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR   = os.path.join(SCRIPT_DIR, "LOGS")
HTML_PATH  = os.path.join(SCRIPT_DIR, "dashboard.html")
PORT       = 8081

with open(os.path.join(SCRIPT_DIR, "config.json"), "r") as f:
    _cfg = json.load(f)

API_KEY    = _cfg["api"]["key"]
API_SECRET = _cfg["api"]["secret"]
STATION_ID = _cfg["api"]["stationId"]

_station_name_cache = None


def _headers():
    return {"x-api-secret": API_SECRET, "Content-Type": "application/json"}


def _station_name():
    global _station_name_cache
    if _station_name_cache:
        return _station_name_cache
    try:
        url  = f"https://api.weatherlink.com/v2/stations?api-key={API_KEY}"
        resp = requests.get(url, headers=_headers(), timeout=10)
        resp.raise_for_status()
        stations = resp.json().get("stations", [])
        for s in stations:
            if str(s.get("station_id")) == str(STATION_ID):
                _station_name_cache = s.get("station_name", "WEATHER STATION").upper()
                return _station_name_cache
        if stations:
            _station_name_cache = stations[0].get("station_name", "WEATHER STATION").upper()
            return _station_name_cache
    except Exception:
        pass
    _station_name_cache = "WEATHER STATION"
    return _station_name_cache


def fetch_current():
    url = f"https://api.weatherlink.com/v2/current/{STATION_ID}?api-key={API_KEY}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=10)
        resp.raise_for_status()
        raw = resp.json()
    except Exception as e:
        return {"error": str(e)}

    data = None
    if "sensors" in raw:
        for sensor in raw.get("sensors", []):
            if sensor.get("data"):
                sd = sensor["data"][0]
                if "temp" in sd and "hum" in sd:
                    data = sd
                    break
    elif "data" in raw:
        arr = raw.get("data", [])
        data = arr[0] if arr else None

    if not data:
        return {"error": "No sensor data in API response"}

    return {
        "_station_name": _station_name(),
        "timestamp":      datetime.utcnow().isoformat(),
        "temp":           data.get("temp"),
        "humidity":       data.get("hum"),
        "dew_point":      data.get("dew_point"),
        "heat_index":     data.get("heat_index"),
        "wet_bulb":       data.get("wet_bulb"),
        "pm_1":           data.get("pm_1"),
        "pm_2p5":         data.get("pm_2p5"),
        "pm_10":          data.get("pm_10"),
        "aqi_val":        data.get("aqi_val"),
        "aqi_desc":       data.get("aqi_desc"),
        "wind_speed":     data.get("wind_speed_last"),
        "wind_gust":      data.get("wind_speed_hi_last_2_min"),
        "wind_dir":       data.get("wind_dir_scalar_avg_last_2_min"),
        "pressure":       data.get("bar_sea_level"),
        "rainfall":       data.get("rain_day_in"),
        "solar_rad":      data.get("solar_rad"),
        "uv_index":       data.get("uv_index"),
        "temp_in":        data.get("temp_in"),
        "hum_in":         data.get("hum_in"),
    }


def fetch_history(days=7):
    if not os.path.exists(LOGS_DIR):
        return []
    cutoff  = datetime.utcnow() - timedelta(days=days)
    records = []
    files   = sorted(glob.glob(os.path.join(LOGS_DIR, "weather_data_*.json")))
    for fp in files[-3:]:
        try:
            with open(fp) as f:
                records.extend(json.load(f))
        except Exception:
            pass
    out = []
    for r in records:
        try:
            ts = datetime.fromisoformat(r.get("timestamp", ""))
            if ts >= cutoff:
                out.append(r)
        except Exception:
            out.append(r)
    return out[-600:]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, body_bytes, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/dashboard.html"):
            try:
                with open(HTML_PATH, "rb") as f:
                    self._html(f.read())
            except FileNotFoundError:
                self._json({"error": "dashboard.html not found"}, 404)
        elif path == "/api/current":
            self._json(fetch_current())
        elif path == "/api/history":
            self._json(fetch_history())
        else:
            self._json({"error": "not found"}, 404)


if __name__ == "__main__":
    if STATION_ID in ("YOUR_STATION_ID", ""):
        print("Warning: STATION_ID not configured in config.json")
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"  Weather Dashboard  →  http://localhost:{PORT}")
    print("  Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
