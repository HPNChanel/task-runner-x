Write-Host "Starting TaskRunnerX development environment..."

# Start Docker services
docker-compose up -d mysql redis

# Wait for MySQL to be ready
Write-Host "Waiting for MySQL to be ready..."
do {
    Start-Sleep -Seconds 2
    $mysqlReady = docker-compose exec mysql mysqladmin ping -h "localhost" --silent 2>$null
} while ($LASTEXITCODE -ne 0)

Write-Host "MySQL is up - continuing..."

# Wait a bit more for full initialization
Start-Sleep -Seconds 5

# Run migrations
alembic upgrade head

# Start services
Start-Process -FilePath "uvicorn" -ArgumentList "taskrunnerx.api.main:app --reload --host 0.0.0.0 --port 8000"
Start-Process -FilePath "python" -ArgumentList "-m taskrunnerx.worker.run_worker"
Start-Process -FilePath "python" -ArgumentList "-m taskrunnerx.scheduler.service"

Write-Host "Services started. API available at http://localhost:8000"
