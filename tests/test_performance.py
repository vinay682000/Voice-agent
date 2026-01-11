"""
Performance Tests for Voice Agent
Measures response times and throughput.
"""
import pytest
import pytest_asyncio
import os
import sys
import time
import statistics
from httpx import AsyncClient, ASGITransport

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """Create FastAPI app instance for testing."""
    from main import app as fastapi_app
    return fastapi_app


class TestPerformance:
    """Performance tests measuring response times."""
    
    @pytest.mark.asyncio
    async def test_config_endpoint_latency(self, app):
        """Measure /config endpoint latency."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            times = []
            for _ in range(10):
                start = time.perf_counter()
                response = await client.get("/config")
                end = time.perf_counter()
                times.append((end - start) * 1000)  # Convert to ms
                assert response.status_code == 200
            
            avg = statistics.mean(times)
            max_time = max(times)
            min_time = min(times)
            
            print(f"\n/config endpoint performance:")
            print(f"  Avg: {avg:.2f}ms")
            print(f"  Min: {min_time:.2f}ms")
            print(f"  Max: {max_time:.2f}ms")
            
            # Should respond in under 100ms
            assert avg < 100, f"Average latency {avg}ms exceeds 100ms threshold"
    
    @pytest.mark.asyncio
    async def test_root_endpoint_latency(self, app):
        """Measure root endpoint latency."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            times = []
            for _ in range(10):
                start = time.perf_counter()
                response = await client.get("/")
                end = time.perf_counter()
                times.append((end - start) * 1000)
                assert response.status_code == 200
            
            avg = statistics.mean(times)
            print(f"\n/ endpoint performance: Avg {avg:.2f}ms")
            assert avg < 100
    
    @pytest.mark.asyncio
    async def test_search_kb_latency(self, app):
        """Measure /search_kb endpoint latency."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            times = []
            queries = ["comfort", "discomfort", "scarcity", "brain", "Michael Easter"]
            
            for query in queries:
                start = time.perf_counter()
                response = await client.post("/search_kb", json={"query": query})
                end = time.perf_counter()
                times.append((end - start) * 1000)
                assert response.status_code == 200
            
            avg = statistics.mean(times)
            max_time = max(times)
            
            print(f"\n/search_kb endpoint performance:")
            print(f"  Avg: {avg:.2f}ms")
            print(f"  Max: {max_time:.2f}ms")
            
            # KB search should respond in under 500ms
            assert avg < 500, f"Average KB search latency {avg}ms exceeds 500ms threshold"


class TestThroughput:
    """Throughput tests measuring requests per second."""
    
    @pytest.mark.asyncio
    async def test_config_throughput(self, app):
        """Measure /config endpoint throughput."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            num_requests = 50
            start = time.perf_counter()
            
            for _ in range(num_requests):
                response = await client.get("/config")
                assert response.status_code == 200
            
            end = time.perf_counter()
            duration = end - start
            rps = num_requests / duration
            
            print(f"\n/config throughput: {rps:.1f} requests/second")
            
            # Should handle at least 50 requests/second
            assert rps > 50, f"Throughput {rps} RPS below 50 threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
