#!/bin/bash
set -e

echo "Starting TaskRunnerX development environment..."

# Start MySQL and Redis
docker-compose up -d mysql redis

# Wait for MySQL to be ready
echo "Waiting for MySQL to be ready..."
until docker-compose exec mysql mysqladmin ping -h "localhost" --silent; do
    echo "MySQL is unavailable - sleeping"
    sleep 2
done

echo "MySQL is up - continuing..."

# Wait a bit more for full initialization
sleep 5

# Run migrations
alembic upgrade head

# Start API in background
uvicorn taskrunnerx.api.main:app --reload --host 0.0.0.0 --port 8000 &

# Start worker in background
python -m taskrunnerx.worker.run_worker &

# Start scheduler
python -m taskrunnerx.scheduler.service &

echo "Services started. API available at http://localhost:8000"
