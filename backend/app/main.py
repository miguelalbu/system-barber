import re
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.db import engine
from app.routers import auth, team, tenants


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Navalha · Core API",
    version="0.1.0",
    description=(
        "System of record for the barbershop SaaS. Multi-tenant with Row-Level "
        "Security isolation; the tenant is resolved from the access domain."
    ),
    lifespan=lifespan,
)

# Allow any subdomain of the base domain — that is where each shop is served.
# A customer's own domain goes into `cors_origins`.
_BASE_DOMAIN = re.escape(settings.base_domain)
ALLOWED_ORIGINS = rf"https?://([a-z0-9-]+\.)?{_BASE_DOMAIN}(:\d+)?"

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tenants.router)
app.include_router(team.router)


@app.get("/health", tags=["infra"], summary="Liveness and database connectivity")
async def health():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok", "environment": settings.environment}
