"""FastAPI application."""

from fastapi import FastAPI

from ..config import config
from ..logging import setup_logging
from .routes import jobs, schedules, system

# Setup logging
setup_logging()

app = FastAPI(
    title="TaskRunnerX API",
    description="Distributed task queue system",
    version="0.1.0"
)

# Include routes
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(schedules.router, prefix="/api/v1/schedules", tags=["schedules"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "TaskRunnerX API", "version": "0.1.0"}


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)
