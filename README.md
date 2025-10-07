# TaskRunnerX

Tiny, production-lean **task runner** built on **FastAPI + MySQL + Redis Streams + APScheduler**.

## Quick start (local)

1. Create venv and install:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
Setup MySQL & Redis (Docker recommended):

docker compose up -d mysql redis
Initialize DB:

python -m taskrunnerx.scripts.init_db
Run API:

python -m taskrunnerx.app.main
Run Worker:

python -m taskrunnerx.worker.worker
Run Scheduler (optional):

python -m taskrunnerx.scheduler.scheduler
```

API
POST /api/tasks → body: { "name": "echo", "payload": { "message": "hi" } }

GET /api/tasks/{id}

GET /api/tasks?limit=50&offset=0

GET /api/health

Notes
MySQL DSN via .env (MYSQL\_\*); driver: PyMySQL.

Redis Streams (trx.tasks) with consumer group (trx.workers).

Worker supports demo tasks: heartbeat, echo, sha256. Extend in worker.py.

## Development workflow

This repository enforces consistent formatting, linting, and type checking across Python and
TypeScript/JavaScript sources. To set up the tooling locally:

```bash
poetry install --no-root
npm install
poetry run pre-commit install
```

Run all quality gates (the same ones executed in CI) with:

```bash
poetry run pre-commit run --all-files
```

If a hook reports formatting issues, re-run it with `--all-files` or invoke targeted commands such as
`poetry run black .`, `npm run lint -- --fix`, or `npm run format:fix` to apply fixes.
