from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.classification import router as classification_router
from app.api.routes.upload import router as upload_router
from app.config.settings import get_settings
from app.database.session import init_db
from app.schemas.activity_schema import APIMessage

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins) or ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api/upload", tags=["upload"])
app.include_router(classification_router, prefix="/api", tags=["classification"])


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health", response_model=APIMessage)
def health() -> APIMessage:
    return APIMessage(status="ok", message="EAC Weekly Timesheet Classification API is running")
