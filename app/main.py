from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db.database import initialize_database
from app.jobs.queue import start_workers, stop_workers
from app.middleware.csrf import CSRFMiddleware
from app.middleware.maintenance import MaintenanceMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.stats import StatsMiddleware
from app.routes import (
    admin_auth,
    admin_banners,
    admin_settings,
    admin_stats,
    ads,
    audio,
    pages,
    synthesize,
    voices,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_database()
    await start_workers()
    try:
        yield
    finally:
        await stop_workers()


app = FastAPI(title="Voice Box", lifespan=lifespan)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(StatsMiddleware)
app.add_middleware(MaintenanceMiddleware)
app.add_middleware(CSRFMiddleware)
app.include_router(pages.router)
app.include_router(synthesize.router)
app.include_router(audio.router)
app.include_router(voices.router)
app.include_router(admin_auth.router)
app.include_router(admin_settings.router)
app.include_router(admin_banners.router)
app.include_router(admin_stats.router)
app.include_router(ads.router)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
DATA_BANNERS = Path(__file__).resolve().parents[1] / "data" / "banners"
DATA_BANNERS.mkdir(parents=True, exist_ok=True)
app.mount("/data/banners", StaticFiles(directory=DATA_BANNERS), name="banners")
