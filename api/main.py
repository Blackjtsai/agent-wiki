# ============================================================
# File: main.py
# Desc: FastAPI main app - lifespan, CORS, router mounts
# Module: api/
# Created: 2026-06-28
# Modified: 2026-06-28 (Layer 6 - checkin router, heartbeat enabled)
# Dev: Blackjtsai
# ============================================================

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import init_pool, close_pool
from api.routers import health, query, wiki_public, checkin
from api.routers import admin_auth, admin_documents, admin_ingest, admin_wiki, admin_jobs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("atwk")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifecycle: init DB pool + APScheduler on startup, close on shutdown."""
    await init_pool()

    from job.scheduler import setup_scheduler
    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("APScheduler started")

    yield

    scheduler.shutdown(wait=False)
    logger.info("APScheduler stopped")
    await close_pool()


app = FastAPI(
    title="Agent Wiki Knowledge Management System (ATWK)",
    description="Intelligent Wiki Knowledge Management System",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(query.router,            prefix="/api")    # Layer 2
app.include_router(wiki_public.router,      prefix="/api")    # Layer 4
app.include_router(checkin.router,          prefix="/api")    # Layer 6
app.include_router(admin_auth.router,       prefix="/admin")  # Layer 3
app.include_router(admin_documents.router,  prefix="/admin")  # Layer 3
app.include_router(admin_ingest.router,     prefix="/admin")  # Layer 3
app.include_router(admin_wiki.router,       prefix="/admin")  # Layer 3
app.include_router(admin_jobs.router,       prefix="/admin")  # Layer 5
