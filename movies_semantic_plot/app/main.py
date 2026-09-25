"""
FastAPI Application — Main Entry Point

Creates the FastAPI instance, wires up:
  - Lifespan events (DB table creation on startup)
  - CORS middleware
  - Custom timing middleware
  - Exception handlers
  - All routers (auth, users, heroes)

Run:  uvicorn app.main:app --reload
Docs: http://127.0.0.1:8000/docs
"""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging
from app.core.cost_tracker import CostTracker
from app.core.error_handler import setup_error_handlers
from app.db import get_database
from app.dependencies import CurrentAdmin
from app.routers import auth, searches, movies, users
from fastapi import FastAPI, Request
from app.core.config import settings


# Database instance (SQLModel engine)
# db = get_database("mysql")
db = get_database(settings.DB_TYPE)


cost_tracker = CostTracker()


# --- Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables. Shutdown: cleanup."""
    db.create_db_and_tables()
    print("Database ready [OK]")
    yield
    print("Shutting down...")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

# --- App Instance ---

app = FastAPI(
    title="FastAPI Tutorial — Organized App",
    description="A multi-file FastAPI project demonstrating best practices.",
    version="1.0.0",
    lifespan=lifespan,
)

# Store cost tracker in app state
app.state.cost_tracker = cost_tracker

# --- Middleware ---

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# # Custom timing middleware
# class TimingMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next) -> Response:
#         request_id = str(uuid.uuid4())
#         start = time.perf_counter()
#         response = await call_next(request)
#         response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}"
#         response.headers["X-Request-ID"] = request_id
#         return response


# app.add_middleware(TimingMiddleware)
setup_error_handlers(app)




# --- Routers ---

app.include_router(auth.router)
app.include_router(searches.router)
app.include_router(movies.router)
app.include_router(users.router)


# --- Root ---

@app.get("/", tags=["root"])
def root():
    """Health check / welcome endpoint."""
    return {"message": "FastAPI Tutorial — Organized App", "docs": "/docs"}

@app.get("/stats")
def get_stats(user:CurrentAdmin):
    return app.state.cost_tracker.get_summary()
