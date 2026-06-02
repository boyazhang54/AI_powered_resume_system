from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.history import router as history_router
from app.api.resumes import router as resumes_router
from app.config import get_settings
from app.services.database import init_db


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-powered resume parsing and job matching service.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resumes_router, prefix="/api", tags=["resumes"])
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(history_router, prefix="/api", tags=["history"])


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": settings.app_name}
