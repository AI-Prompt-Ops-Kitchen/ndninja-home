# Content Worker — Celery worker for ninja_content.py video generation
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ninja_content.py writes to PROJECT_DIR/output (= /app/output)
# Volume mount is at /data/output — symlink so files land on the mount
RUN ln -s /data/output /app/output

COPY celery_app.py tasks.py ./

CMD ["celery", "-A", "celery_app", "worker", "-l", "info", "-c", "2", "-Q", "content", "-n", "content@%h"]
