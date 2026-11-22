import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from backend.database import create_tables, DB_DIALECT
from backend.routes import chat, upload, documents, speech

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("backend.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables are created
    logger.info("Initializing %s on dialect %s...", settings.APP_NAME, DB_DIALECT)
    create_tables()
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Multimodal AI Companion with RAG, Vision, Audio, and Emotional Support.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(documents.router)
app.include_router(speech.router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "database_dialect": DB_DIALECT,
        "environment": settings.APP_ENV
    }
