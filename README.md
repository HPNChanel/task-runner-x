# TaskRunnerX

Tiny, production-lean **task runner** built on **FastAPI + MySQL + Redis Streams + APScheduler**.

## Quick start (local)

1) Create venv and install:

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
API
POST /api/tasks → body: { "name": "echo", "payload": { "message": "hi" } }

GET /api/tasks/{id}

GET /api/tasks?limit=50&offset=0

GET /api/health

Notes
MySQL DSN via .env (MYSQL_*); driver: PyMySQL.

Redis Streams (trx.tasks) with consumer group (trx.workers).

Worker supports demo tasks: heartbeat, echo, sha256. Extend in worker.py.
