from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app import models
from backend.app.database import Base, engine
from backend.app.routers.calls import router as calls_router
from backend.app.routers.cases import router as cases_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(calls_router)
app.include_router(cases_router)


@app.get("/health")
def health():
    return {"status": "healthy"}