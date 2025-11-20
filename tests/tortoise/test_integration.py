"""
Integration tests for Tortoise ORM with Nexios using in-memory SQLite.
"""

import pytest
from tortoise.models import Model
from tortoise import fields

from nexios import NexiosApp
from nexios.testclient import TestClient
from nexios_contrib.tortoise import init_tortoise, get_tortoise_client


# Test models
class User(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    email = fields.CharField(max_length=255, unique=True)
    age = fields.IntField(null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "users"


class Post(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=200)
    content = fields.TextField()
    author = fields.ForeignKeyField("models.User", related_name="posts")
    published = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "posts"


class TestTortoiseIntegration:
    """Integration tests for Tortoise ORM with Nexios."""

    @pytest.fixture
    async def app(self):
        """Create a test app with Tortoise ORM."""
        app = NexiosApp(title="Test App")
        
        # Initialize Tortoise with in-memory SQLite
        init_tortoise(
            app,
            db_url="sqlite://:memory:",
            modules={"models": [__name__]},  # Use current module for models
            generate_schemas=True,
            add_exception_handlers=True,
        )
        
        # Manually trigger startup to initialize Tortoise
        await app._startup()
        
        yield app
        
        # Cleanup - trigger shutdown
        await app._shutdown()

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_basic_crud_operations(self, app, client):
        """Test basic CRUD operations through HTTP endpoints."""
        
        @app.get("/users")
        async def list_users(request, response):
            users = await User.all()
            return response.json([
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "age": user.age,
                    "is_active": user.is_active
                }
                for user in users
            ])
        
        @app.post("/users")
        async def create_user(request, response):
            data = await request.json
            user = await User.create(**data)
            return response.status(201).json({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "age": user.age,
                "is_active": user.is_active
            })
        
        @app.get("/users/{user_id}")
        async def get_user(request, response):
            user_id = int(request.path_params["user_id"])
            try:
                user = await User.get(id=user_id)
                return response.json({
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "age": user.age,
                    "is_active": user.is_active
                })
            except User.DoesNotExist:
                raise  # Will be handled by exception handler
        
        @app.put("/users/{user_id}")
        async def update_user(request, response):
            user_id = int(request.path_params["user_id"])
            data = await request.json
            
            try:
                user = await User.get(id=user_id)
                for key, value in data.items():
                    setattr(user, key, value)
                await user.save()
                
                return response.json({
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "age": user.age,
                    "is_active": user.is_active
                })
            except User.DoesNotExist:
                raise  # Will be handled by exception handler
        
        @app.delete("/users/{user_id}")
        async def delete_user(request, response):
            user_id = int(request.path_params["user_id"])
            try:
                user = await User.get(id=user_id)
                await user.delete()
                return response.status(204)
            except User.DoesNotExist:
                raise  # Will be handled by exception handler
        
        # Test CREATE
        create_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "is_active": True
        }
        create_resp = client.post("/users", json=create_data)
        assert create_resp.status_code == 201
        user_data = create_resp.json()
        user_id = user_data["id"]
        assert user_data["name"] == "John Doe"
        assert user_data["email"] == "john@example.com"
        
        # Test READ (list)
        list_resp = client.get("/users")
        assert list_resp.status_code == 200
        users = list_resp.json()
        assert len(users) == 1
        assert users[0]["name"] == "John Doe"
        
        # Test READ (single)
        get_resp = client.get(f"/users/{user_id}")
        assert get_resp.status_code == 200
        user_data = get_resp.json()
        assert user_data["name"] == "John Doe"
        
        # Test UPDATE
        update_data = {"name": "Jane Doe", "age": 25}
        update_resp = client.put(f"/users/{user_id}", json=update_data)
        assert update_resp.status_code == 200
        updated_user = update_resp.json()
        assert updated_user["name"] == "Jane Doe"
        assert updated_user["age"] == 25
        assert updated_user["email"] == "john@example.com"  # Should remain unchanged
        
        # Test DELETE
        delete_resp = client.delete(f"/users/{user_id}")
        assert delete_resp.status_code == 204
        
        # Verify deletion
        list_resp = client.get("/users")
        assert list_resp.status_code == 200
        users = list_resp.json()
        assert len(users) == 0

    def test_foreign_key_relationships(self, app, client):
        """Test foreign key relationships."""
        
        @app.post("/users")
        async def create_user(request, response):
            data = await request.json
            user = await User.create(**data)
            return response.status(201).json({"id": user.id, "name": user.name})
        
        @app.post("/posts")
        async def create_post(request, response):
            data = await request.json
            author = await User.get(id=data["author_id"])
            post = await Post.create(
                title=data["title"],
                content=data["content"],
                author=author,
                published=data.get("published", False)
            )
            return response.status(201).json({
                "id": post.id,
                "title": post.title,
                "author_id": author.id
            })
        
        @app.get("/posts/{post_id}")
        async def get_post_with_author(request, response):
            post_id = int(request.path_params["post_id"])
            post = await Post.get(id=post_id).select_related("author")
            return response.json({
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "published": post.published,
                "author": {
                    "id": post.author.id,
                    "name": post.author.name,
                    "email": post.author.email
                }
            })
        
        # Create user
        user_resp = client.post("/users", json={
            "name": "Author User",
            "email": "author@example.com"
        })
        assert user_resp.status_code == 201
        user_id = user_resp.json()["id"]
        
        # Create post
        post_resp = client.post("/posts", json={
            "title": "Test Post",
            "content": "This is a test post",
            "author_id": user_id,
            "published": True
        })
        assert post_resp.status_code == 201
        post_id = post_resp.json()["id"]
        
        # Get post with author
        get_resp = client.get(f"/posts/{post_id}")
        assert get_resp.status_code == 200
        post_data = get_resp.json()
        assert post_data["title"] == "Test Post"
        assert post_data["author"]["name"] == "Author User"
        assert post_data["author"]["id"] == user_id

    def test_exception_handling_integration(self, app, client):
        """Test that Tortoise exceptions are properly handled."""
        
        @app.post("/users")
        async def create_user(request, response):
            data = await request.json
            user = await User.create(**data)
            return response.status(201).json({"id": user.id})
        
        @app.get("/users/{user_id}")
        async def get_user(request, response):
            user_id = int(request.path_params["user_id"])
            user = await User.get(id=user_id)  # Will raise DoesNotExist
            return response.json({"id": user.id})
        
        # Test IntegrityError (duplicate email)
        user_data = {"name": "Test User", "email": "test@example.com"}
        
        # First creation should succeed
        resp1 = client.post("/users", json=user_data)
        assert resp1.status_code == 201
        
        # Second creation with same email should fail with IntegrityError
        resp2 = client.post("/users", json=user_data)
        assert resp2.status_code == 400
        error_data = resp2.json()
        assert error_data["type"] == "integrity_error"
        assert "Integrity constraint violation" in error_data["error"]
        
        # Test DoesNotExist
        resp3 = client.get("/users/999")
        assert resp3.status_code == 404
        error_data = resp3.json()
        assert error_data["type"] == "not_found_error"
        assert "Record not found" in error_data["error"]

   

   