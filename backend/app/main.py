"""Creates the FastAPI app and registers the modules. Nothing else lives here."""

import re
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.modules.identity.router import routers as identity_routers


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

register_exception_handlers(app)

for router in identity_routers:
    app.include_router(router)


@app.get("/health", tags=["infra"], summary="Liveness and database connectivity")
async def health():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok", "environment": settings.environment}
