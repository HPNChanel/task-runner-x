# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Security
- Pin Docker base images to `python:3.11.9-slim@sha256:2856e6af199e8128161abd320575eb9b341f3b76f017b5d0c9cd364f60d8a050` for reproducible builds.
- Add Syft SBOM generation to CI and enforce dependency pinning through Poetry.

### Dependency Updates
- Bump FastAPI to 0.116.2 to consume Starlette 0.48.0 and resolve GHSA-2c2j-9gv5-cj73.
- Update pydantic to 2.11.10 and pydantic-settings to 2.11.0 for compatibility fixes.
- Upgrade SQLAlchemy to 2.0.43 and PyMySQL to 1.1.2 for the latest 2.x/1.x maintenance releases.
- Move redis to 5.3.1 and APScheduler to 3.11.0 for current bug fixes without major changes.
- Raise python-dotenv to 1.1.1 and requests to 2.32.5 to address GHSA-9hjg-9r4m-mvj7.
- Introduce Poetry-managed dev dependencies for black 24.10.0 and ruff 0.7.2.
