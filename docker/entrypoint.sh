#!/bin/sh
set -e

# Generate config.json from environment variables if not already mounted
if [ ! -f /app/config.json ]; then
  python3 - <<'EOF'
import json, os, sys

missing = [v for v in ('WL_API_KEY', 'WL_API_SECRET', 'WL_STATION_ID') if not os.environ.get(v)]
if missing:
    print(f"[entrypoint] ERROR: required env vars not set: {', '.join(missing)}", flush=True)
    sys.exit(1)

recipients_raw = os.environ.get('WL_EMAIL_RECIPIENTS', '')
recipients = [r.strip() for r in recipients_raw.split(',') if r.strip()]

cfg = {
    'api': {
        'key':       os.environ['WL_API_KEY'],
        'secret':    os.environ['WL_API_SECRET'],
        'stationId': os.environ['WL_STATION_ID'],
    },
    'email': {
        'sender_email':    os.environ.get('WL_EMAIL_SENDER', ''),
        'sender_password': os.environ.get('WL_EMAIL_PASSWORD', ''),
        'recipient_email': recipients,
        'smtp_server':     'smtp.gmail.com',
        'smtp_port':       587,
    },
}

fd = os.open('/app/config.json', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, 'w') as f:
    json.dump(cfg, f, indent=4)

print('[entrypoint] config.json written from environment variables', flush=True)
EOF
  chown appuser:appuser /app/config.json
fi

# Start cron daemon (runs wl_logger.py on schedule)
cron

# Run the dashboard server in the foreground (becomes PID 1 via exec,
# so /proc/1/fd/1 used by cron jobs routes to docker logs)
exec gosu appuser python3 /app/wl_dashboard.py
