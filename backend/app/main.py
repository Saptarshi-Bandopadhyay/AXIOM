"""Main FastAPI application entry point for ReproCheck backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI Research Methodology Reviewer API",
    version="0.1.0",
    debug=settings.DEBUG,
)

# Enable CORS for frontend web client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 routes
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify backend service availability."""
    return {"status": "ok", "service": "reprocheck-backend"}


# Mount static frontend production build if available
import os
from fastapi.staticfiles import StaticFiles

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.isdir(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

