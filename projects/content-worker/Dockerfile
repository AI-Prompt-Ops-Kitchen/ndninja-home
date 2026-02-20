# Content Worker — Celery worker for ninja_content.py video generation
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY celery_app.py tasks.py ./

CMD ["celery", "-A", "celery_app", "worker", "-l", "info", "-c", "2", "-Q", "content", "-n", "content@%h"]
