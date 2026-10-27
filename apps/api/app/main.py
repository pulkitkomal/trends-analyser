from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routes import auth, topics
from app.services.seed import seed_example_topic

app = FastAPI(title="trends-analyser", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(topics.router, prefix="/api")
app.include_router(auth.router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    seed_example_topic()


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}
