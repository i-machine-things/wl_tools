FROM python:3.11-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends cron gosu \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd -r appuser \
 && useradd -r -g appuser -d /app -s /bin/sh appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appuser /app \
 && chmod +x /app/docker/entrypoint.sh \
 && chmod 0644 /app/docker/crontab \
 && crontab -u appuser /app/docker/crontab

EXPOSE 8081

ENTRYPOINT ["/app/docker/entrypoint.sh"]
