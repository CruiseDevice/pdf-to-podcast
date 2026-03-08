from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import podcasts, health
from app.database import init_db

app = FastAPI(
    title="PDF to Podcast API",
    description="Convert PDF documents to podcast audio",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(podcasts.router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    init_db()
