
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router
from src.database.db import (
    initialize_database,
    get_connection,
    save_transaction,
)


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

        # Check whether the database contains transactions.
        with get_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM transactions"
            ).fetchone()[0]

        # Seed one synthetic demo transaction if empty.
        if count == 0:
            demo_transaction = {
                "step": 1,
                "transactionType": "TRANSFER",
                "amount": 19824.90,
                "initiator": "DEMO_CUSTOMER_001",
                "oldBalInitiator": 187718.18,
                "newBalInitiator": 167893.28,
                "recipient": "DEMO_CUSTOMER_002",
                "oldBalRecipient": 8.31,
                "newBalRecipient": 19833.21,
            }

            transaction_id = save_transaction(demo_transaction)

            logger.info(
                "Demo transaction created with ID: %s",
                transaction_id,
            )
        else:
            logger.info(
                "Database already contains %s transactions. "
                "Demo seeding skipped.",
                count,
            )

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
