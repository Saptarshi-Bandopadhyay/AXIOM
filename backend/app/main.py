"""Main application entry point for ReproCheck backend.

Provides the FastAPI application instance, middleware configuration,
and foundational system endpoints such as health checks.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

# Retrieve application configuration settings
settings = get_settings()

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI Research Methodology Reviewer API",
    version="0.1.0",
    debug=settings.DEBUG,
)

# Configure Cross-Origin Resource Sharing (CORS) for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify backend service availability.

    Returns:
        dict[str, str]: Status indicator dictionary.
    """
    return {"status": "ok", "service": "reprocheck-backend"}
