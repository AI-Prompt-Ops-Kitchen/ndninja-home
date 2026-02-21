FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
    && git config --system safe.directory '*'

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY client.py .

EXPOSE 8050

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8050", "--workers", "1"]
