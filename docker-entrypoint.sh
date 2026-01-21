#!/bin/bash
set -e

echo "🚀 Starting Aruba Bank Contract Management System..."

# Wait for database to be ready (already handled by healthcheck, but extra safety)
echo "⏳ Waiting for database..."
sleep 5

#Reset the database to updates on the seed scripts
echo "🔄 Resetting database..."
python reset.py

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Seed initial users if database is empty
echo "🌱 Checking if users need to be seeded..."
python seed_users.py

# Seed vendors and contracts if database is empty
echo "🌱 Checking if vendors and contracts need to be seeded..."
python seed_vendors_contracts.py

echo "✅ Initialization complete!"
echo "🌐 Starting application server..."

# Start the application with newrelic and timestamps
exec newrelic-admin run-program uvicorn main:root_app --host 0.0.0.0 --port 8000 2>&1 | ts '[%Y-%m-%d %H:%M:%S]'

