"""
app/main.py
-----------
Entry point for the KNIME Data Loader API.

Run with:
    uvicorn app.main:app --reload --port 8000
    (from the backend/ directory)
"""

import logging
import logging.config

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import batches, operations
from app.db import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="KNIME Data Loader",
    description="Flexible JSON ingestion + batch validation/load for QAD Cloud ERP",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(batches.router)
app.include_router(operations.router)


@app.on_event("startup")
def on_startup():
    """Initialize database schema on startup."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database ready")


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
def root():
    """API root."""
    return {
        "app": "KNIME Data Loader",
        "endpoints": {
            "POST /api/upload-json": "Ingest JSON batch",
            "GET /api/batches": "List all batches",
            "GET /api/batch/{batch_id}": "Inspect raw batch payload",
            "GET /api/debug/last": "Get most recent batch",
            "POST /api/validate": "Validate batch(es)",
            "POST /api/load": "Load batch(es) into QAD",
            "GET /health": "Health check",
        },
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting server on 0.0.0.0:8000")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)