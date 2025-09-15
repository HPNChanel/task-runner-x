#!/bin/bash
set -e

echo "Initializing Alembic..."

alembic init taskrunnerx/storage/migrations

echo "Alembic initialized."
