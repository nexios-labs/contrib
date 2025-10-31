# Redis Integration Tests

This directory contains comprehensive integration tests for the Nexios Redis contrib module.

## Test Structure

```
test_redis/
├── __init__.py                     # Test package initialization
├── conftest.py                     # Test fixtures and configuration
├── test_redis_client.py            # RedisClient class tests
├── test_redis_config.py            # RedisConfig class tests
├── test_redis_integration.py       # Nexios app integration tests
├── test_redis_dependencies.py      # Dependency injection tests
├── test_redis_utils.py             # Utility functions tests
├── test_redis_real_integration.py  # Real Redis server tests
├── run_redis_tests.py              # Test runner script
└── README.md                       # This file
```

## Test Categories

### 1. Unit Tests (Mocked Redis)
- **test_redis_client.py**: Tests RedisClient functionality with mocked Redis
- **test_redis_config.py**: Tests RedisConfig validation and conversion
- **test_redis_dependencies.py**: Tests dependency injection functions
- **test_redis_utils.py**: Tests utility functions
- **test_redis_integration.py**: Tests Nexios app integration with mocked Redis

### 2. Integration Tests (Real Redis)
- **test_redis_real_integration.py**: Tests with actual Redis server

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install pytest pytest-asyncio redis
```

### Quick Start

Run unit tests (no Redis server required):
```bash
python tests/test_redis/run_redis_tests.py --mode unit
```

Run integration tests (requires Redis server):
```bash
python tests/test_redis/run_redis_tests.py --mode integration
```

Run all tests:
```bash
python tests/test_redis/run_redis_tests.py --mode all
```

### Manual Test Execution

Run specific test files:
```bash
# Unit tests
pytest tests/test_redis/test_redis_client.py -v
pytest tests/test_redis/test_redis_config.py -v
pytest tests/test_redis/test_redis_integration.py -v

# Integration tests (requires Redis)
pytest tests/test_redis/test_redis_real_integration.py -v -m integration
```

Run with coverage:
```bash
pytest tests/test_redis/ --cov=nexios_contrib.redis --cov-report=html
```

## Redis Server Setup

### Using Docker (Recommended)
```bash
# Start Redis server
docker run -d -p 6379:6379 --name redis-test redis:latest

# Verify connection
docker exec redis-test redis-cli ping
# Should return: PONG

# Stop and remove when done
docker stop redis-test && docker remove redis-test
```

### Local Installation

**macOS (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

## Test Features

### Comprehensive Coverage
- ✅ Redis client connection management
- ✅ Basic operations (GET, SET, DELETE, EXISTS)
- ✅ Expiration and TTL operations
- ✅ Counter operations (INCR, DECR)
- ✅ Hash operations (HGET, HSET, HGETALL)
- ✅ List operations (LPUSH, RPUSH, LPOP, RPOP, LLEN)
- ✅ Set operations (SADD, SMEMBERS, SREM, SCARD)
- ✅ JSON operations (with fallback)
- ✅ Raw command execution
- ✅ Error handling and recovery
- ✅ Configuration validation
- ✅ Environment variable configuration
- ✅ Nexios app integration
- ✅ Dependency injection
- ✅ Utility functions
- ✅ Session management patterns
- ✅ Caching patterns
- ✅ Counter patterns

### Mock vs Real Testing
- **Unit tests** use mocked Redis for fast, reliable testing without external dependencies
- **Integration tests** use real Redis server to verify actual functionality
- Both test suites cover the same functionality to ensure consistency

### Test Patterns
- **Fixtures**: Reusable test setup and teardown
- **Parameterized tests**: Testing multiple scenarios efficiently
- **Error simulation**: Testing error handling and recovery
- **Real-world scenarios**: Session management, caching, counters
- **Performance considerations**: Connection pooling, async operations

## Configuration

### Test Database
Integration tests use Redis database 15 to avoid conflicts with development data.

### Environment Variables
Tests can be configured using environment variables:
```bash
export REDIS_URL="redis://localhost:6379"
export REDIS_DB="15"
export REDIS_PASSWORD=""  # If required
```

### Pytest Markers
- `@pytest.mark.integration`: Marks tests that require real Redis server
- Tests without this marker use mocked Redis

## Troubleshooting

### Common Issues

**Redis Connection Refused:**
```
redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379. Connection refused.
```
- Solution: Start Redis server (see setup instructions above)

**Import Error:**
```
ImportError: No module named 'redis'
```
- Solution: `pip install redis`

**Permission Denied:**
```
PermissionError: [Errno 13] Permission denied
```
- Solution: Check Redis server permissions or use Docker

### Debug Mode
Run tests with verbose output:
```bash
pytest tests/test_redis/ -v -s --tb=long
```

### Test Isolation
Each test cleans up after itself:
- Unit tests reset mock state
- Integration tests use `FLUSHDB` on test database (15)

## Contributing

When adding new Redis functionality:

1. **Add unit tests** with mocked Redis in appropriate test file
2. **Add integration tests** in `test_redis_real_integration.py` if needed
3. **Update fixtures** in `conftest.py` if new test patterns are needed
4. **Test both success and error cases**
5. **Follow existing test patterns** for consistency

### Test Naming Convention
- `test_<functionality>_<scenario>`: e.g., `test_redis_get_existing_key`
- `test_<functionality>_error_<error_type>`: e.g., `test_redis_get_connection_error`

### Mock Patterns
```python
# Mock Redis operation
mock_redis.get.return_value = "expected_value"
result = await redis_client.get("test_key")
assert result == "expected_value"
mock_redis.get.assert_called_with("test_key")

# Mock Redis error
mock_redis.get.side_effect = RedisOperationError("Connection failed")
with pytest.raises(RedisOperationError):
    await redis_client.get("test_key")
```