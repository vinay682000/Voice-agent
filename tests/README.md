# Voice Agent Test Suite

This folder contains comprehensive tests for the Voice Agent application.

## Test Categories

| Category | File | Description |
|----------|------|-------------|
| Unit Tests | `test_unit.py` | Tests for individual functions |
| Integration Tests | `test_integration.py` | API endpoint tests |
| Performance Tests | `test_performance.py` | Latency and throughput |
| Security Tests | `test_security.py` | SAST and vulnerability checks |
| Stress Tests | `test_stress.py` | High load testing |

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx bandit

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run security scan (SAST)
bandit -r . -f json -o tests/results/bandit_report.json
```

## Results

Test results are saved in the `results/` subfolder.
