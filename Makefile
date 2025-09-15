.PHONY: fmt lint test up down migrate
fmt:
\tpoetry run ruff check --fix .
\tpoetry run black .
lint:
\tpoetry run ruff check .
\tpoetry run mypy taskrunnerx
test:
\tpoetry run pytest -q
up:
\tdocker compose up -d --build
down:
\tdocker compose down -v
migrate:
\tpoetry run alembic upgrade head