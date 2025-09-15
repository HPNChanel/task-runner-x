#!/bin/bash
set -e

echo "Seeding demo data..."

# Submit demo jobs
taskrunnerx job submit echo --message "Demo job 1"
taskrunnerx job submit sleep --seconds 10

# Create demo schedule
taskrunnerx schedule create --name "hourly-echo" --cron "0 * * * *" --task echo --args '{"message": "Hourly task"}'

echo "Demo data seeded."
