#!/bin/bash
set -e

echo "Resetting database..."

# Drop and recreate database
alembic downgrade base
alembic upgrade head

echo "Database reset complete."
