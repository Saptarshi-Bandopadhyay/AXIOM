"""Tests for health check endpoint."""

from httpx import ASGITransport, AsyncClient
from app.main import app


async def test_health_check() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok", "service": "reprocheck-backend"}
