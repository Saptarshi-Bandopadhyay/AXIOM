"""Unit tests for the health check endpoint."""

from httpx import ASGITransport, AsyncClient
from app.main import app


async def test_health_check_returns_ok() -> None:
    """Verify that GET /health returns HTTP 200 with service status."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "reprocheck-backend"


async def test_root_serves_frontend_spa() -> None:
    """Verify that GET / returns the built React SPA index.html."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert "ReproCheck" in response.text
    assert '<div id="root">' in response.text
