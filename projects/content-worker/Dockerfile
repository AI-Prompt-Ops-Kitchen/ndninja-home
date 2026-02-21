# Content Worker — Celery worker for ninja_content.py video generation
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev gcc \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ninja_content.py writes to PROJECT_DIR/output (= /app/output)
# Volume mount is at /data/output — symlink so files land on the mount
RUN ln -s /data/output /app/output

COPY celery_app.py tasks.py ./
COPY tests/ ./tests/

# Preflight + entrypoint for fail-fast boot validation
COPY preflight.sh entrypoint.sh /app/
RUN chmod +x /app/preflight.sh /app/entrypoint.sh

HEALTHCHECK --interval=60s --timeout=10s --retries=3 --start-period=15s \
    CMD /app/preflight.sh

ENTRYPOINT ["/app/entrypoint.sh"]
