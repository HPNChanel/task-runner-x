.PHONY: init run api worker scheduler fmt lint

init:
\tpython -m taskrunnerx.scripts.init_db

run:
\tuvicorn taskrunnerx.app.main:app --host 0.0.0.0 --port 8000 --reload

api:
\tpython -m taskrunnerx.app.main

worker:
\tpython -m taskrunnerx.worker.worker

scheduler:
\tpython -m taskrunnerx.scheduler.scheduler

fmt:
\tpython -m black taskrunnerx

lint:
\tpython -m ruff check taskrunnerx
