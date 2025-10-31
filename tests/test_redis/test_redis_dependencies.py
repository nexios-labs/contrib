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
    RedisDepend, RedisOperationDepend, RedisKeyDepend, RedisCacheDepend
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
        async def get_value(request: Request,response, redis=RedisDepend()):
            key = request.path_params["key"]
            value = await redis.get(key)
            return {"key": key, "value": value}
        
        mock_redis.get.return_value = "test_value"
        
        response = test_client_with_redis.get("/cache/mykey")
        assert response.status_code == 200
        assert response.json() == {"key": "mykey", "value": "test_value"}
        mock_redis.get.assert_called_with("mykey")    
    def test_redis_operation_depend_get(self, test_client_with_redis, mock_redis):
        """Test RedisOperationDepend with GET operation."""
        app = test_client_with_redis.app
        
        @app.get("/direct-get/{key}")
        async def direct_get(
            request: Request,
            response: Response,
            value=RedisOperationDepend("get", "test_key")
        ):
            # Value should be the result of redis.get("test_key")
            return {"value": value}
        
        mock_redis.get.return_value = "direct_value"
        
        response = test_client_with_redis.get("/direct-get/test_key")
        assert response.status_code == 200
        assert response.json() == {"value": "direct_value"}
        mock_redis.get.assert_called_with("test_key")
    

    

    

    def test_redis_key_depend_get_default(self, test_client_with_redis, mock_redis):
        """Test RedisKeyDepend with GET operation and default value."""
        app = test_client_with_redis.app
        
        @app.get("/user/{user_id}")
        async def get_user(
            request: Request,
            response: Response,
            user_data=RedisKeyDepend("user:123", "get", {"name": "Unknown"})
        ):
            return {"user": user_data}
        
        # Test with existing key
        mock_redis.get.return_value = "John Doe"
        response = test_client_with_redis.get("/user/123")
        assert response.status_code == 200
        assert response.json() == {"user": "John Doe"}
        
        # Test with non-existing key (returns None)
        mock_redis.get.return_value = None
        response = test_client_with_redis.get("/user/123")
        assert response.status_code == 200
        assert response.json() == {"user": {"name": "Unknown"}}

   
    def test_redis_key_depend_exists(self, test_client_with_redis, mock_redis):
        """Test RedisKeyDepend with EXISTS operation."""
        app = test_client_with_redis.app
        
        @app.get("/check/{key}")
        async def check_key(
            request: Request,
            response: Response,
            exists=RedisKeyDepend("check_key", "exists", 0)
        ):
            return {"exists": bool(exists)}
        
        # Test existing key
        mock_redis.exists.return_value = 1
        response = test_client_with_redis.get("/check/test")
        assert response.status_code == 200
        assert response.json() == {"exists": True}
        
        # Test non-existing key
        mock_redis.exists.return_value = 0
        response = test_client_with_redis.get("/check/test")
        assert response.status_code == 200
        assert response.json() == {"exists": False}

    def test_redis_key_depend_ttl(self, test_client_with_redis, mock_redis):
        """Test RedisKeyDepend with TTL operation."""
        app = test_client_with_redis.app
        
        @app.get("/ttl/{key}")
        async def get_ttl(
            request: Request,
            response: Response,
            ttl=RedisKeyDepend("ttl_key", "ttl", -1)
        ):
            return {"ttl": ttl}
        
        # Test key with TTL
        mock_redis.ttl.return_value = 300
        response = test_client_with_redis.get("/ttl/test")
        assert response.status_code == 200
        assert response.json() == {"ttl": 300}
        
        # Test key without TTL
        mock_redis.ttl.return_value = -1
        response = test_client_with_redis.get("/ttl/test")
        assert response.status_code == 200
        assert response.json() == {"ttl": -1}

    def test_redis_key_depend_error_fallback(self, test_client_with_redis, mock_redis):
        """Test RedisKeyDepend error handling with fallback to default."""
        app = test_client_with_redis.app
        
        @app.get("/error-test")
        async def error_test(
            request: Request,
            response: Response,
            value=RedisKeyDepend("error_key", "get", "fallback_value")
        ):
            return {"value": value}
        
        # Mock Redis to raise an exception
        from nexios_contrib.redis.client import RedisOperationError
        mock_redis.get.side_effect = RedisOperationError("Connection error")
        
        response = test_client_with_redis.get("/error-test")
        assert response.status_code == 200
        assert response.json() == {"value": "fallback_value"}

    def test_redis_cache_depend_basic(self, test_client_with_redis, mock_redis):
        """Test RedisCacheDepend basic functionality."""
        app = test_client_with_redis.app
        
        @app.get("/cached/{param}")
        async def cached_operation(
            request: Request,
            response:Response,
            result=RedisCacheDepend("expensive:test", ttl=600)
        ):
            return {"result": result}
        
        # Test with cached value
        mock_redis.get.return_value = "cached_result"
        response = test_client_with_redis.get("/cached/test")
        assert response.status_code == 200
        assert response.json() == {"result": "cached_result"}
        mock_redis.get.assert_called_with("expensive:test")
        
        # Test without cached value
        mock_redis.get.return_value = None
        response = test_client_with_redis.get("/cached/test")
        assert response.status_code == 200
        assert response.json() == {"result": "cached_expensive:test"}

    def test_multiple_redis_dependencies(self, test_client_with_redis, mock_redis):
        """Test multiple Redis dependencies in single route."""
        app = test_client_with_redis.app
        
        @app.get("/multi-deps")
        async def multi_deps(
            request,
            response,
            redis=RedisDepend(),
            counter_value=RedisOperationDepend("get", "counter"),
            user_exists=RedisKeyDepend("user:123", "exists", 0),
            cached_data=RedisCacheDepend("cache:data", ttl=300)
        ):
            return {
                "redis_available": redis is not None,
                "counter": counter_value,
                "user_exists": bool(user_exists),
                "cached": cached_data
            }
        
        # Mock Redis responses
        mock_redis.get.side_effect = ["5", None]  # counter value, then cache miss
        mock_redis.exists.return_value = 1
        
        response = test_client_with_redis.get("/multi-deps")
        assert response.status_code == 200
        data = response.json()
        assert data["redis_available"] is True
        assert data["counter"] == "5"
        assert data["user_exists"] is True
        assert data["cached"] == "cached_cache:data"

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