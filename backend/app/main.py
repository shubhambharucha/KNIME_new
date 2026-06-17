"""
app/main.py
-------------
Entry point. Run with: uvicorn app.main:app --reload --port 8000
(from the backend/ directory).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import batches, operations, settings
from app.db import init_db

app = FastAPI(title="KNIME Data Loader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(batches.router)
app.include_router(operations.router)
app.include_router(settings.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
