import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from db import init_db
from routers import router


def _get_origin_allowlist() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "").strip()
    return [p.strip() for p in raw.split(",") if p.strip()]


def _origin_allowed(origin: str | None, allowlist: list[str]) -> bool:
    if not origin or not origin.strip():
        return True
    if not allowlist:
        return True
    return origin.strip() in allowlist


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Idea Generator API",
    description=(
        "Generate five project ideas from user interests and strengths, "
        "store each request in SQLite, and protect endpoints with an API key."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

_origin_allowlist = _get_origin_allowlist()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origin_allowlist if _origin_allowlist else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def restrict_origin(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    origin = request.headers.get("origin")
    if origin and not _origin_allowed(origin, _origin_allowlist):
        return JSONResponse(
            status_code=403,
            content={"detail": "Origin not allowed."},
        )
    return await call_next(request)


app.include_router(router)