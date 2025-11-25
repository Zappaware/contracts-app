#FROM registry.arubabank.com/container/python:base-latest
FROM python:3.12-slim
WORKDIR /app

# Install moreutils for ts command and libmagic1 for python-magic
RUN apt-get update && apt-get install -y moreutils libmagic1 && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt newrelic

# Copy application code
COPY . .

# Start with Uvicorn, pipe through ts for timestamps
CMD ["sh", "-c", "newrelic-admin run-program uvicorn main:root_app --host 0.0.0.0 --port 8000 2>&1 | ts '[%Y-%m-%d %H:%M:%S]'"]
