
import uvicorn
from fastapi import FastAPI

from .api.routes import router as api_router
from .config import get_settings
from .services.queue import queue

settings = get_settings()
app = FastAPI(title=settings.app_name)


@app.on_event("startup")
async def on_startup():
    await queue.connect()


@app.on_event("shutdown")
async def on_shutdown():
    await queue.close()


app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run("taskrunnerx.app.main:app", host=settings.host, port=settings.port, reload=True)
