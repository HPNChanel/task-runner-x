# TaskRunnerX

A distributed task queue system built with Redis Streams, FastAPI, and MySQL.

## Features

- Distributed job processing with Redis Streams
- RESTful API for job management
- Cron-based scheduling
- Worker auto-scaling
- Dead letter queue handling
- Idempotency guarantees

## Quick Start

```bash
# Copy environment file
cp .env.example .env

# Start services
make dev-up

# Submit a job
taskrunnerx job submit echo --message "Hello World"

# Check job status
taskrunnerx job list
```

## Architecture

- **API**: FastAPI web server for job submission
- **Scheduler**: APScheduler for cron-based jobs
- **Workers**: Process jobs from Redis Streams
- **Storage**: MySQL for persistence
