"""
Stress Tests for Voice Agent
High-load testing to find breaking points.
"""
import pytest
import pytest_asyncio
import asyncio
import os
import sys
import time
from httpx import AsyncClient, ASGITransport

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """Create FastAPI app instance for testing."""
    from main import app as fastapi_app
    return fastapi_app


class TestStress:
    """Stress tests with concurrent requests."""
    
    @pytest.mark.asyncio
    async def test_concurrent_config_requests(self, app):
        """Test /config endpoint with concurrent requests."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            num_concurrent = 20
            
            async def make_request():
                response = await client.get("/config")
                return response.status_code
            
            start = time.perf_counter()
            tasks = [make_request() for _ in range(num_concurrent)]
            results = await asyncio.gather(*tasks)
            end = time.perf_counter()
            
            success_count = sum(1 for r in results if r == 200)
            duration = end - start
            
            print(f"\nConcurrent /config stress test:")
            print(f"  Requests: {num_concurrent}")
            print(f"  Success: {success_count}/{num_concurrent}")
            print(f"  Duration: {duration:.2f}s")
            
            # All requests should succeed
            assert success_count == num_concurrent, f"Only {success_count}/{num_concurrent} succeeded"
    
    @pytest.mark.asyncio
    async def test_concurrent_kb_search_requests(self, app):
        """Test /search_kb endpoint with concurrent requests."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            num_concurrent = 10
            queries = ["comfort", "discomfort", "brain", "scarcity", "challenge"]
            
            async def make_request(query):
                response = await client.post("/search_kb", json={"query": query})
                return response.status_code
            
            start = time.perf_counter()
            tasks = [make_request(queries[i % len(queries)]) for i in range(num_concurrent)]
            results = await asyncio.gather(*tasks)
            end = time.perf_counter()
            
            success_count = sum(1 for r in results if r == 200)
            duration = end - start
            
            print(f"\nConcurrent /search_kb stress test:")
            print(f"  Requests: {num_concurrent}")
            print(f"  Success: {success_count}/{num_concurrent}")
            print(f"  Duration: {duration:.2f}s")
            
            assert success_count == num_concurrent
    
    @pytest.mark.asyncio
    async def test_rapid_fire_requests(self, app):
        """Test rapid sequential requests."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            num_requests = 100
            success_count = 0
            
            start = time.perf_counter()
            for _ in range(num_requests):
                response = await client.get("/config")
                if response.status_code == 200:
                    success_count += 1
            end = time.perf_counter()
            
            duration = end - start
            rps = num_requests / duration
            
            print(f"\nRapid fire test:")
            print(f"  Requests: {num_requests}")
            print(f"  Success: {success_count}")
            print(f"  RPS: {rps:.1f}")
            
            # Should handle at least 80% success rate
            assert success_count >= num_requests * 0.8
    
    @pytest.mark.asyncio
    async def test_mixed_endpoint_stress(self, app):
        """Test multiple endpoints simultaneously."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            
            async def get_config():
                return await client.get("/config")
            
            async def get_root():
                return await client.get("/")
            
            async def search_kb():
                return await client.post("/search_kb", json={"query": "test"})
            
            # Mix of different requests
            tasks = []
            for _ in range(5):
                tasks.append(get_config())
                tasks.append(get_root())
                tasks.append(search_kb())
            
            start = time.perf_counter()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end = time.perf_counter()
            
            errors = [r for r in results if isinstance(r, Exception)]
            success = [r for r in results if not isinstance(r, Exception) and r.status_code == 200]
            
            print(f"\nMixed endpoint stress test:")
            print(f"  Total: {len(tasks)}")
            print(f"  Success: {len(success)}")
            print(f"  Errors: {len(errors)}")
            print(f"  Duration: {end - start:.2f}s")
            
            # Should have minimal errors
            assert len(errors) == 0, f"Errors occurred: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
