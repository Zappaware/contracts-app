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

# Convert line endings and make executable (safe for both Windows and Linux)
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

# Convert line endings and make executable (safe for both Windows and Linux)
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

# Use entrypoint script to run migrations and seed data before starting app
ENTRYPOINT ["./docker-entrypoint.sh"]
