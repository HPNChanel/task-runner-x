#!/bin/bash
set -e

echo "Stopping TaskRunnerX services..."

# Kill background processes
pkill -f "uvicorn taskrunnerx.api.main"
pkill -f "taskrunnerx.worker.run_worker"
pkill -f "taskrunnerx.scheduler.service"

echo "Services stopped."
