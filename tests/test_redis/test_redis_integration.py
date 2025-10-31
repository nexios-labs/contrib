"""
Integration tests for Redis with Nexios application.
"""
import pytest
from unittest.mock import AsyncMock, patch

from nexios import NexiosApp, Depend
from nexios.http import Request, Response
from nexios.testclient import TestClient

from nexios_contrib.redis import (
    init_redis, get_redis, get_redis_client, RedisConnectionError
)


class TestRedisIntegration:
    """Test Redis integration with Nexios application."""

    def test_init_redis_basic(self):
        """Test basic Redis initialization."""
        app = NexiosApp()
        
        # Initialize Redis
        init_redis(app)
        
        # Check that Redis client is stored in app state
        assert "redis" in app.state
        assert app.state["redis"] is not None

    def test_init_redis_with_custom_config(self):
        """Test Redis initialization with custom configuration."""
        app = NexiosApp()
        
        # Initialize Redis with custom settings
        init_redis(
            app,
            url="redis://localhost:6380",
            db=2,
            password="test_password",
            decode_responses=False,
            socket_timeout=15.0
        )
        
        # Check configuration
        redis_client = app.state["redis"]
        assert redis_client.config.url == "redis://localhost:6380"
        assert redis_client.config.db == 2
        assert redis_client.config.password == "test_password"
        assert redis_client.config.decode_responses is False
        assert redis_client.config.socket_timeout == 15.0

    async def test_get_redis_dependency(self, app_with_mock_redis):
        """Test get_redis dependency injection."""
        redis_client = get_redis()
        
        assert redis_client is not None
        assert hasattr(redis_client, 'get')
        assert hasattr(redis_client, 'set')

    async def test_get_redis_client_alias(self, app_with_mock_redis):
        """Test get_redis_client alias."""
        redis_client = get_redis_client()
        
        assert redis_client is not None
        assert redis_client == get_redis()

    def test_get_redis_not_initialized(self):
        """Test get_redis when Redis is not initialized."""
        # Clear global Redis client
        import nexios_contrib.redis
        original_client = nexios_contrib.redis._redis_client
        nexios_contrib.redis._redis_client = None
        
        try:
            with pytest.raises(RedisConnectionError, match="Redis client not initialized"):
                get_redis()
        finally:
            # Restore original client
            nexios_contrib.redis._redis_client = original_client

    
    
    def test_redis_list_operations_route(self, test_client_with_redis, mock_redis):
        """Test Redis list operations in routes."""
        app = test_client_with_redis.app
        
        @app.post("/messages")
        async def add_message(request: Request, response,redis=Depend(get_redis)):
            data = await request.json
            message = data.get("message")
            
            length = await redis.lpush("messages", message)
            return {"message": message, "queue_length": length}
        
        @app.get("/messages/next")
        async def get_next_message(request: Request,response, redis=Depend(get_redis)):
            message = await redis.rpop("messages")
            if not message:
                return {"message": None}
            
            return {"message": message}
        
        @app.get("/messages/count")
        async def get_message_count(request: Request, response, redis=Depend(get_redis)):
            count = await redis.llen("messages")
            return {"count": count}
        
        # Mock Redis responses
        mock_redis.lpush.return_value = 3
        mock_redis.rpop.return_value = "Hello World"
        mock_redis.llen.return_value = 2
        
        # Test add message
        response = test_client_with_redis.post(
            "/messages",
            json={"message": "Hello World"}
        )
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World", "queue_length": 3}
        
        # Test get next message
        response = test_client_with_redis.get("/messages/next")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}
        
        # Test get message count
        response = test_client_with_redis.get("/messages/count")
        assert response.status_code == 200
        assert response.json() == {"count": 2}

    def test_redis_hash_operations_route(self, test_client_with_redis, mock_redis):
        """Test Redis hash operations in routes."""
        app = test_client_with_redis.app
        
        @app.post("/user/{user_id}/profile")
        async def update_profile(request: Request, response,redis=Depend(get_redis)):
            user_id = request.path_params["user_id"]
            data = await request.json
            
            profile_key = f"profile:{user_id}"
            
            for field, value in data.items():
                await redis.hset(profile_key, field, str(value))
            
            return {"user_id": user_id, "status": "updated"}
        
        @app.get("/user/{user_id}/profile")
        async def get_profile(request: Request, response,redis=Depend(get_redis)):
            user_id = request.path_params["user_id"]
            profile_key = f"profile:{user_id}"
            
            profile = await redis.hgetall(profile_key)
            return {"user_id": user_id, "profile": profile}
        
        # Mock Redis responses
        mock_redis.hset.return_value = 1
        mock_redis.hgetall.return_value = {"name": "John Doe", "email": "john@example.com"}
        
        # Test update profile
        response = test_client_with_redis.post(
            "/user/123/profile",
            json={"name": "John Doe", "email": "john@example.com"}
        )
        assert response.status_code == 200
        assert response.json() == {"user_id": "123", "status": "updated"}
        
        # Test get profile
        response = test_client_with_redis.get("/user/123/profile")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "123"
        assert data["profile"]["name"] == "John Doe"
        assert data["profile"]["email"] == "john@example.com"

   

    @patch('nexios_contrib.redis.client.RedisClient.connect')
    async def test_startup_connection_success(self, mock_connect):
        """Test successful Redis connection on app startup."""
        app = NexiosApp()
        init_redis(app)
        
        # Mock successful connection
        mock_connect.return_value = None
        
        # Simulate app startup
        for handler in app.startup_handlers:
            await handler()
        
        mock_connect.assert_called_once()

    @patch('nexios_contrib.redis.client.RedisClient.connect')
    async def test_startup_connection_failure(self, mock_connect):
        """Test Redis connection failure on app startup."""
        app = NexiosApp()
        init_redis(app)
        
        # Mock connection failure
        mock_connect.side_effect = Exception("Connection failed")
        
        # Simulate app startup - should raise RedisConnectionError
        with pytest.raises(RedisConnectionError, match="Failed to connect to Redis"):
            for handler in app.startup_handlers:
                await handler()

    @patch('nexios_contrib.redis.client.RedisClient.close')
    async def test_shutdown_cleanup(self, mock_close):
        """Test Redis cleanup on app shutdown."""
        app = NexiosApp()
        init_redis(app)
        
        # Mock successful close
        mock_close.return_value = None
        
        # Simulate app shutdown
        for handler in app.shutdown_handlers:
            await handler()
        
        mock_close.assert_called_once()