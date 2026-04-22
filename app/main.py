from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes import router as task_router
from app.db.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Task Tracker API",
    description="Внутренний сервис для команды разработки",
    lifespan=lifespan,
)

app.include_router(task_router)


@app.get("/ping", tags=["Status"])
async def ping():
    return {"status": "ok"}
