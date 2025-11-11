import requests
import json
import csv
import os
from datetime import datetime
import time
"""
This script fetches current weather data from the WeatherLink API and logs it to a CSV file.

set poll interval useing crontab -e
# Every 5 minutes
*/5 * * * * /usr/bin/python3 /path/to/script.py

# Every 10 minutes
*/10 * * * * /usr/bin/python3 /path/to/script.py

# Every 30 minutes
*/30 * * * * /usr/bin/python3 /path/to/script.py

# Every hour
0 * * * * /usr/bin/python3 /path/to/script.py

# Every 6 hours
0 */6 * * * /usr/bin/python3 /path/to/script.py

# Every day at 9 AM
0 9 * * * /usr/bin/python3 /path/to/script.py
"""
# Configuration
now = datetime.now()

with open(os.path.join(os.path.dirname(__file__), "config.json"), "r") as f:
    config = json.load(f)

API_KEY = config["api"]["key"]
API_SECRET = config["api"]["secret"]
STATION_ID = config["api"]["stationId"]

# Create LOGS directory if it doesn't exist
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(SCRIPT_DIR, 'LOGS')
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOGS_DIR, f'weather_data_{now.strftime("%b_%Y")}.csv')
JSON_LOG = os.path.join(LOGS_DIR, f'weather_data_{now.strftime("%b_%Y")}.json')
MAX_RETRIES = 3
RETRY_DELAY = 5

def get_headers():
    """Get headers with API authentication"""
    return {
        "x-api-secret": API_SECRET,
        "Content-Type": "application/json"
    }

def get_station_list():
    """Fetch all available stations for the API account"""
    url = f"https://api.weatherlink.com/v2/stations?api-key={API_KEY}"
    headers = get_headers()
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch station list: {e}")
        return None

def display_available_stations():
    """Display all available station IDs and their details"""
    print("\nFetching available weather stations...")
    print("-" * 80)
    
    response = get_station_list()
    if not response or "stations" not in response:
        print("Could not retrieve station list. Check your API credentials.")
        return
    
    stations = response.get("stations", [])
    
    if not stations:
        print("No stations found for this API account.")
        return
    
    print(f"\nFound {len(stations)} station(s):\n")
    
    for i, station in enumerate(stations, 1):
        station_id = station.get("station_id")
        name = station.get("station_name", "N/A")
        location = station.get("location", {})
        city = location.get("city", "N/A")
        state = location.get("state", "N/A")
        country = location.get("country", "N/A")
        active = "Active" if station.get("active") else "Inactive"
        
        print(f"{i}. Station ID: {station_id}")
        print(f"   Name: {name}")
        print(f"   Location: {city}, {state}, {country}")
        print(f"   Status: {active}")
        print()

def get_current_conditions():
    """Fetch current weather conditions from WeatherLink API v2"""
    url = f"https://api.weatherlink.com/v2/current/{STATION_ID}?api-key={API_KEY}"
    headers = get_headers()
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                print(f"API request failed (attempt {attempt + 1}): {e}")
                time.sleep(RETRY_DELAY)
            else:
                print(f"Failed to fetch data after {MAX_RETRIES} attempts: {e}")
                return None

def extract_data(api_response):
    """Extract relevant weather data from API response"""
    if not api_response:
        return None
    
    # Debug: Print the response structure
    print(f"API Response keys: {api_response.keys() if isinstance(api_response, dict) else 'Not a dict'}")
    
    # Handle sensor-based response (current format)
    if "sensors" in api_response:
        sensors = api_response.get("sensors", [])
        if not sensors:
            return None
        
        # Find the weather sensor (sensor_type 326 for environmental data)
        data = None
        for sensor in sensors:
            if sensor.get("data"):
                sensor_data = sensor["data"][0]
                # Look for temp field which indicates weather data
                if "temp" in sensor_data and "hum" in sensor_data:
                    data = sensor_data
                    break
        
        if not data:
            return None
    # Handle legacy direct data response
    elif "data" in api_response:
        data_array = api_response.get("data", [])
        if not data_array:
            return None
        data = data_array[0] if isinstance(data_array, list) else data_array
    else:
        print(f"Unexpected response structure: {api_response}")
        return None
    
    timestamp = datetime.now().isoformat()
    
    # Map field names from the API response
    extracted = {
        "timestamp": timestamp,
        "temp": data.get("temp"),
        "humidity": data.get("hum"),
        "dew_point": data.get("dew_point"),
        "heat_index": data.get("heat_index"),
        "wet_bulb": data.get("wet_bulb"),
        "pm_1": data.get("pm_1"),
        "pm_2p5": data.get("pm_2p5"),
        "pm_10": data.get("pm_10"),
        "aqi_val": data.get("aqi_val"),
        "aqi_desc": data.get("aqi_desc"),
        "wind_speed": None,  # Not in this sensor
        "wind_gust": None,
        "wind_dir": None,
        "pressure": None,
        "rainfall": None,
        "solar_radiation": None,
        "uv_index": None,
    }
    
    return extracted

def save_to_csv(data, filename=LOG_FILE):
    """Append data to CSV file"""
    if not data:
        return
    
    file_exists = os.path.isfile(filename)
    
    try:
        with open(filename, "a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
        print(f"Data saved to {filename}")
    except IOError as e:
        print(f"Error writing to CSV: {e}")

def save_to_json(data, filename=JSON_LOG):
    """Append data to JSON file"""
    if not data:
        return
    
    try:
        records = []
        if os.path.isfile(filename):
            with open(filename, "r") as f:
                records = json.load(f)
        
        records.append(data)
        
        with open(filename, "w") as f:
            json.dump(records, f, indent=2)
        print(f"Data saved to {filename}")
    except IOError as e:
        print(f"Error writing to JSON: {e}")

def format_csv_display(data):
    """Format data for nice display"""
    if not data:
        return ""
    
    display = f"Temp: {data.get('temp')}°C | Humidity: {data.get('humidity')}% | "
    display += f"Dew Point: {data.get('dew_point')}°C | "
    display += f"Heat Index: {data.get('heat_index')}°C | "
    display += f"AQI: {data.get('aqi_val')} ({data.get('aqi_desc')}) | "
    display += f"PM2.5: {data.get('pm_2p5')} | PM10: {data.get('pm_10')}"
    return display

def log_data():
    """Single data fetch and logging function"""
    print(f"[{datetime.now()}] Fetching weather data...")
    
    api_response = get_current_conditions()
    if api_response:
        data = extract_data(api_response)
        if data:
            print(format_csv_display(data))
            
            save_to_csv(data)
            save_to_json(data)
            print("Data logged successfully")
        else:
            print("No data extracted from API response")
    else:
        print("Failed to fetch data from API")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--list-stations":
        display_available_stations()
    else:
        if STATION_ID == "YOUR_STATION_ID":
            print("Error: Please configure STATION_ID")
            print("Use: python script.py --list-stations")
            print("to see all available station IDs")
        else:
            log_data()