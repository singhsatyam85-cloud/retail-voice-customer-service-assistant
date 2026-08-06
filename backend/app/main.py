from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app import models
from backend.app.config import get_settings
from backend.app.database import Base, engine
from backend.app.middleware.request_size_limit import RequestSizeLimitMiddleware
from backend.app.routers.calls import router as calls_router
from backend.app.routers.cases import router as cases_router
from backend.app.routers.voice_support import router as voice_support_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

# Middleware order matters: add_middleware inserts at position 0, so the
# LAST call below is the outermost layer. The size limit must stay inside
# CORS -- otherwise a 413 goes out without Access-Control-Allow-Origin and
# the browser reports an opaque network error instead of the real status.
# Rejects oversized bodies before FastAPI parses multipart or resolves the
# authentication dependency. The 10 MB audio-content rule in
# services/voice_support.py remains as defence in depth.
app.add_middleware(RequestSizeLimitMiddleware)

# Narrow, configurable origin allowlist -- required because the
# voice-support endpoints read an Authorization header, so "*" cannot be
# used here. Production origins must be set via CORS_ALLOWED_ORIGINS.
# Must remain the last add_middleware call (outermost layer).
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calls_router)
app.include_router(cases_router)
app.include_router(voice_support_router)


@app.get("/health")
def health():
    return {"status": "healthy"}