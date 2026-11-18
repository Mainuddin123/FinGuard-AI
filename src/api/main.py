
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router
from src.database.db import initialize_database


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing FinGuard AI database...")

    try:
        initialize_database()
        logger.info("FinGuard AI database initialized successfully.")
    except Exception:
        logger.exception("Database initialization failed.")
        raise

    yield

    logger.info("FinGuard AI application shutting down.")


app = FastAPI(
    title="FinGuard AI API",
    description="Transaction investigation API with human review.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "service": "FinGuard AI",
        "status": "running",
        "docs": "/docs",
    }
