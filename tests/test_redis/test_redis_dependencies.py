"""
Integration tests for Redis dependency injection.
"""
import pytest
from unittest.mock import AsyncMock

from nexios import NexiosApp, Depend
from nexios.http import Request, Response
from nexios.testclient import TestClient
from nexios.dependencies import Context

from nexios_contrib.redis.dependency import (
    RedisDepend
)


class TestRedisDependencies:
    """Test Redis dependency injection functions."""

    def test_redis_depend_basic(self, test_client_with_redis, mock_redis):
        """Test basic RedisDepend functionality."""
        app = test_client_with_redis.app
        
        @app.get("/test")
        async def test_endpoint(request,response,redis=RedisDepend()):
            # Redis client should be injected
            assert redis is not None
            assert hasattr(redis, 'get')
            return {"status": "ok"}
        
        response = test_client_with_redis.get("/test")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_redis_depend_in_route(self, test_client_with_redis, mock_redis):
        """Test RedisDepend in actual route usage."""
        app = test_client_with_redis.app
        
        @app.get("/cache/{key}")
        async def get_value(request: Request,response,key, redis=RedisDepend()):
            value = await redis.get(key)
            return {"key": key, "value": value}
        
        mock_redis.get.return_value = "test_value"
        
        response = test_client_with_redis.get("/cache/mykey")
        assert response.status_code == 200
        assert response.json() == {"key": "mykey", "value": "test_value"}
        mock_redis.get.assert_called_with("mykey")    


    def test_redis_depend_with_context(self, app_with_mock_redis, mock_redis):
        """Test Redis dependencies with explicit context."""
        from nexios_contrib.redis.dependency import RedisDepend
        from nexios.dependencies import Context
        
        # Create a dependency function
        redis_dep = RedisDepend()
        
        # Create a mock context
        context = Context()
        
        # Call the dependency function
        redis_client = redis_dep.dependency(context)
        
        assert redis_client is not None
        assert hasattr(redis_client, 'get')
        assert hasattr(redis_client, 'set')