"""
Integration Tests for Voice Agent API
Tests API endpoints using httpx test client.
"""
import pytest
import pytest_asyncio
import os
import sys
from httpx import AsyncClient, ASGITransport

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """Create FastAPI app instance for testing."""
    # Import here to avoid module-level import issues
    from main import app as fastapi_app
    return fastapi_app


@pytest.mark.asyncio
async def test_root_endpoint(app):
    """Test that root endpoint returns HTML."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_config_endpoint(app):
    """Test /config endpoint returns expected structure."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "hostname" in data
        assert "deployment" in data
        assert "apiKey" in data


@pytest.mark.asyncio
async def test_config_hostname_format(app):
    """Test that hostname in /config doesn't have protocol prefix."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/config")
        data = response.json()
        hostname = data.get("hostname", "")
        assert not hostname.startswith("https://")
        assert not hostname.startswith("http://")


@pytest.mark.asyncio
async def test_search_kb_endpoint_valid(app):
    """Test /search_kb endpoint with valid query."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/search_kb",
            json={"query": "comfort zone"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data


@pytest.mark.asyncio
async def test_search_kb_endpoint_empty_query(app):
    """Test /search_kb endpoint with empty query."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/search_kb",
            json={"query": ""}
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_search_kb_endpoint_no_body(app):
    """Test /search_kb endpoint with missing body (should fail)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/search_kb")
        assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.asyncio
async def test_session_endpoint_structure(app):
    """Test /session endpoint returns expected structure (may fail without valid Azure creds)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/session")
        # This might return 200 or error depending on Azure connectivity
        # We just check it returns JSON
        assert response.headers.get("content-type", "").startswith("application/json")


@pytest.mark.asyncio
async def test_nonexistent_endpoint(app):
    """Test that nonexistent endpoint returns 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/nonexistent")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
