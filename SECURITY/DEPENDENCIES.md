# Dependency Risk Assessment

| Package | Current Version | Latest Safe (Same Major) | Notes |
| --- | --- | --- | --- |
| fastapi | 0.116.2 | 0.116.2 | Upgraded to pull in Starlette >=0.48.0 and remediate GHSA-2c2j-9gv5-cj73 via transitive dependency. |
| starlette (transitive) | 0.48.0 | 0.48.0 | Pulled in through FastAPI upgrade; addresses GHSA-2c2j-9gv5-cj73 (path traversal). |
| uvicorn | 0.30.6 | 0.30.6 | Already at latest patch within 0.30.x. |
| pydantic | 2.11.10 | 2.11.10 | Updated for compatibility with FastAPI 0.116.x and latest bug fixes. |
| pydantic-settings | 2.11.0 | 2.11.0 | Updated to latest release in major line. |
| SQLAlchemy | 2.0.43 | 2.0.43 | Updated to newest 2.0.x maintenance release for security and ORM fixes. |
| PyMySQL | 1.1.2 | 1.1.2 | Patched release with TLS fixes; no known CVEs outstanding. |
| redis | 5.3.1 | 5.3.1 | Latest 5.x train (6.x introduces breaking API changes). |
| APScheduler | 3.11.0 | 3.11.0 | Latest 3.x with scheduler bugfixes. |
| python-dotenv | 1.1.1 | 1.1.1 | Latest 1.x release. |
| requests | 2.32.5 | 2.32.5 | Updated to remediate GHSA-9hjg-9r4m-mvj7 (redirect bypass). |
| black (dev) | 24.10.0 | 24.10.0 | Added to Poetry dev dependencies for deterministic formatting. |
| ruff (dev) | 0.7.2 | 0.7.2 | Added to Poetry dev dependencies for linting parity. |

## Supply Chain Notes
- `pip-audit` previously reported CVEs in `requests 2.32.3` (GHSA-9hjg-9r4m-mvj7) and transitive `starlette 0.40.0` (GHSA-2c2j-9gv5-cj73). Both are resolved via the upgrades above.
- All production dependencies are now pinned in both `pyproject.toml`, `requirements.txt`, and the generated `poetry.lock` to prevent drift.
- Docker base images are pinned to `python:3.11.9-slim@sha256:2856e6af199e8128161abd320575eb9b341f3b76f017b5d0c9cd364f60d8a050` for reproducibility.
- GitHub Actions CI now generates an SBOM using Syft and uploads it as an artifact for downstream review.
- `pip-audit` still reports GHSA-4xh5-x5gv-qwph for the tooling package `pip`; this affects the build image only and is tracked upstream.
