# WeatherLink Data Logger

A lightweight Python suite for logging weather data from the WeatherLink API v2 and receiving automated email reports.

## Features

- **Real-time Weather Logging**: Captures temperature, humidity, dew point, heat index, and air quality data
- **Dual Format Storage**: Saves data to both CSV (for Excel) and JSON (for databases)
- **Automated Email Reports**: Send weather data and CSV exports via email on schedule
- **Cron-Based Scheduling**: Set polling intervals using your system's crontab

## Requirements

- Python 3.7+
- `requests` library
- Gmail account (for email functionality)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/i-machine-things/wl_tools.git
cd wl_tools
```

2. Install dependencies:
```bash
pip install requests
```

3. Get your WeatherLink API credentials from [WeatherLink Account Settings](https://weatherlink.com/account/api)

## Quick Start

### 1. Configure the Logger

Edit `config.json` and update these fields:
```json
"api":{
        "key":"YOUR_API_KEY",
        "secret":"YOUR_API_SECRET",
        "stationId":"YOUR_STATION_ID"
    }
```

### 2. Find Your Station ID

List all available stations:
```bash
python3 wl_logger.py --list-stations
```

This will display all your weather stations with their IDs, names, and locations.

### 3. Test the Logger

Run once to verify everything works:
```bash
python3 wl_logger.py
```

You should see output like:
```
[2025-11-09 02:24:36] Fetching weather data...
Temp: 60.8°C | Humidity: 63.8% | Dew Point: 48.5°C | Heat Index: 59.7°C | AQI: 21.9 (Good) | PM2.5: 10.96 | PM10: 11.13
Data saved to weather_data_<month>_<year>.csv
Data saved to weather_data_<month>_<year>.json
Data logged successfully
```

## Scheduling with Crontab

Set up automated data collection using crontab:

```bash
crontab -e
```

Add one of these lines to schedule your polling interval:

```bash
# Every 5 minutes
*/5 * * * * /usr/bin/python3 /path/to/wl_logger.py

# Every 10 minutes
*/10 * * * * /usr/bin/python3 /path/to/wl_logger.py

# Every 30 minutes
*/30 * * * * /usr/bin/python3 /path/to/wl_logger.py

# Every hour
0 * * * * /usr/bin/python3 /path/to/wl_logger.py

# Every 6 hours
0 */6 * * * /usr/bin/python3 /path/to/wl_logger.py

# Every day at 9 AM
0 9 * * * /usr/bin/python3 /path/to/wl_logger.py
```

**Replace `/path/to/wl_logger.py` with the full path to your script.** Find it with:
```bash
pwd
```

## Email Reports

### Configure Email Sender

Edit `config.json` and update:
```json
"email":{
        "sender_email": "example@gmail.com",
        "sender_password": "app-specific-password",
        "recipient_email": ["example1@gmail.com", "example2@gmail.com"],
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587
    }
```

**Important**: For Gmail, use an [app-specific password](https://support.google.com/accounts/answer/185833), not your regular Gmail password.

### Send Email Manually

```bash
python3 wl_report.py
```

### Schedule Automatic Emails

Add to crontab:

```bash
# Daily email at 8 PM
0 20 * * * /usr/bin/python3 /path/to/wl_report.py

# Weekly email every Monday at 9 AM
0 9 * * 1 /usr/bin/python3 /path/to/wl_report.py

# Every morning at 7 AM
0 7 * * * /usr/bin/python3 /path/to/wl_report.py

# Twice daily (7 AM and 7 PM)
0 7,19 * * * /usr/bin/python3 /path/to/wl_report.py
```

## Files Generated

- **weather_data.csv**: Human-readable CSV file with weather data (opens in Excel)
- **weather_data.json**: JSON format for database integration

### CSV Columns

- `timestamp`: ISO 8601 formatted date/time
- `temp`: Temperature (°C)
- `humidity`: Relative humidity (%)
- `dew_point`: Dew point (°C)
- `heat_index`: Heat index (°C)
- `wet_bulb`: Wet bulb temperature (°C)
- `pm_1`: Particulate matter 1µm
- `pm_2p5`: Particulate matter 2.5µm
- `pm_10`: Particulate matter 10µm
- `aqi_val`: Air Quality Index value
- `aqi_desc`: Air Quality description

## API Authentication

WeatherLink API v2 uses:
- **API Key** as a URL parameter
- **API Secret** in the `x-api-secret` header

Both are required for authentication.

## Troubleshooting

### "401 Unauthorized" Error
- Verify your API key and secret are correct
- Check that your station ID is valid
- Confirm your API credentials have access to the station

### "No data extracted from API response"
- Run `python3 wl_logger.py --list-stations` to verify your setup
- Check that your weather station is online and reporting data

### Email Not Sending
- Verify your email and password are correct
- For Gmail users: Use an [app-specific password](https://support.google.com/accounts/answer/185833)
- Check that SMTP port 587 is not blocked by your firewall

### Crontab Not Running
- Verify the full path to Python: `which python3`
- Verify the full path to your script: `pwd`
- Check crontab logs: `grep CRON /var/log/syslog`

## Example Workflow

1. **Log data every 30 minutes**:
   ```bash
   # Add to crontab
   */30 * * * * /usr/bin/python3 /home/user/weatherLink/wl_logger.py
   ```

2. **Email CSV every Monday morning**:
   ```bash
   # Add to crontab
   0 9 * * 1 /usr/bin/python3 /home/user/weatherLink/wl_report.py
   ```

3. **Open CSV in Excel**: Download your email attachment and open `weather_data_<month>_<year>.csv`

## License

GNU GENERAL PUBLIC LICENSE - see LICENSE file for details

## Support

For issues with the WeatherLink API itself, visit [WeatherLink Documentation](https://weatherlink.com/account/api)

For script issues, open an issue on GitHub.