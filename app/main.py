import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import app.models  # noqa: F401 — registers models with Base.metadata
from app.config import settings
from app.database import Base, engine, get_db
from app.logger import logger
from app.routers import bids, clients
from app.services.csv_import import import_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    yield


app = FastAPI(
    title="Bid Risk Manager",
    description="API for managing bids and assessing risk",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(clients.router)
app.include_router(bids.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        "%s %s → %s (%.0fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": settings.app_name}


@app.post("/import", tags=["Data"])
def run_import(db: Session = Depends(get_db)):
    return import_all(db)
