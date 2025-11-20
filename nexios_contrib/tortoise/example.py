"""
Example usage of Nexios Tortoise ORM integration.

This example demonstrates how to set up and use Tortoise ORM with Nexios,
including model definition, route handlers, and exception handling.
"""
from nexios import NexiosApp
from nexios.http import Request, Response
from nexios_contrib.tortoise import init_tortoise, get_tortoise_client

# Import Tortoise ORM components
from tortoise.models import Model
from tortoise import fields

# Define models
class User(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    email = fields.CharField(max_length=255, unique=True)
    age = fields.IntField(null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "users"
        
    def __str__(self):
        return f"User(id={self.id}, name={self.name})"


class Post(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=200)
    content = fields.TextField()
    author = fields.ForeignKeyField("models.User", related_name="posts")
    published = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "posts"
        
    def __str__(self):
        return f"Post(id={self.id}, title={self.title})"


# Create Nexios app
app = NexiosApp(title="Tortoise ORM Example API", version="1.0.0")

# Initialize Tortoise ORM
init_tortoise(
    app,
    db_url="sqlite://example.db",
    modules={"models": ["__main__"]},  # Use current module
    generate_schemas=True,
    add_exception_handlers=True,
)


# Route handlers
@app.get("/")
async def root(request: Request, response: Response):
    """Root endpoint with API information."""
    return response.json({
        "message": "Nexios Tortoise ORM Example API",
        "version": "1.0.0",
        "endpoints": {
            "users": "/users",
            "posts": "/posts",
            "health": "/health"
        }
    })


@app.get("/health")
async def health_check(request: Request, response: Response):
    """Health check endpoint that tests database connectivity."""
    try:
        # Get Tortoise client and test database connection
        tortoise = get_tortoise_client()
        result = await tortoise.execute_query("SELECT 1 as test")
        return response.json({
            "status": "healthy",
            "database": "connected",
            "test_query": result[0] if result else None
        })
    except Exception as e:
        return response.status(503).json({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        })


@app.get("/users")
async def list_users(request: Request, response: Response):
    """List all users with optional filtering."""
    # Get query parameters
    active_only = request.query_params.get("active", "").lower() == "true"
    limit = int(request.query_params.get("limit", "100"))
    
    # Build query
    query = User.all()
    if active_only:
        query = query.filter(is_active=True)
    
    users = await query.limit(limit)
    
    return response.json([
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "age": user.age,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
        for user in users
    ])


@app.get("/users/{user_id}")
async def get_user(request: Request, response: Response):
    """Get a specific user by ID."""
    user_id = int(request.path_params["user_id"])
    
    try:
        user = await User.get(id=user_id)
        # Fetch related posts
        posts = await Post.filter(author=user)
        
        return response.json({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "age": user.age,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "posts_count": len(posts),
            "posts": [
                {
                    "id": post.id,
                    "title": post.title,
                    "published": post.published,
                    "created_at": post.created_at.isoformat()
                }
                for post in posts
            ]
        })
    except User.DoesNotExist:
        # This will be handled by the automatic exception handler
        # and return a 404 response
        raise


@app.post("/users")
async def create_user(request: Request, response: Response):
    """Create a new user."""
    data = await request.json()
    
    try:
        user = await User.create(
            name=data["name"],
            email=data["email"],
            age=data.get("age"),
            is_active=data.get("is_active", True)
        )
        
        return response.status(201).json({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "age": user.age,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        })
    except Exception:
        # IntegrityError (duplicate email) will be handled automatically
        # and return a 400 response
        raise


@app.put("/users/{user_id}")
async def update_user(request: Request, response: Response):
    """Update an existing user."""
    user_id = int(request.path_params["user_id"])
    data = await request.json()
    
    try:
        user = await User.get(id=user_id)
        
        # Update fields if provided
        if "name" in data:
            user.name = data["name"]
        if "email" in data:
            user.email = data["email"]
        if "age" in data:
            user.age = data["age"]
        if "is_active" in data:
            user.is_active = data["is_active"]
            
        await user.save()
        
        return response.json({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "age": user.age,
            "is_active": user.is_active,
            "updated_at": user.updated_at.isoformat()
        })
    except User.DoesNotExist:
        raise


@app.delete("/users/{user_id}")
async def delete_user(request: Request, response: Response):
    """Delete a user."""
    user_id = int(request.path_params["user_id"])
    
    try:
        user = await User.get(id=user_id)
        await user.delete()
        
        return response.status(204)
    except User.DoesNotExist:
        raise


@app.get("/posts")
async def list_posts(request: Request, response: Response):
    """List all posts with author information."""
    published_only = request.query_params.get("published", "").lower() == "true"
    limit = int(request.query_params.get("limit", "50"))
    
    query = Post.all().select_related("author")
    if published_only:
        query = query.filter(published=True)
    
    posts = await query.limit(limit)
    
    return response.json([
        {
            "id": post.id,
            "title": post.title,
            "content": post.content[:200] + "..." if len(post.content) > 200 else post.content,
            "published": post.published,
            "created_at": post.created_at.isoformat(),
            "author": {
                "id": post.author.id,
                "name": post.author.name,
                "email": post.author.email
            }
        }
        for post in posts
    ])


@app.post("/posts")
async def create_post(request: Request, response: Response):
    """Create a new post."""
    data = await request.json()
    
    try:
        # Verify author exists
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
            "content": post.content,
            "published": post.published,
            "created_at": post.created_at.isoformat(),
            "author_id": author.id
        })
    except User.DoesNotExist:
        return response.status(400).json({
            "error": "Author not found",
            "detail": f"User with id {data['author_id']} does not exist"
        })


@app.get("/stats")
async def get_stats(request: Request, response: Response):
    """Get database statistics using raw SQL."""
    try:
        # Get Tortoise client and execute raw SQL queries
        tortoise = get_tortoise_client()
        user_stats = await tortoise.execute_query(
            "SELECT COUNT(*) as total_users, "
            "COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_users, "
            "AVG(age) as avg_age FROM users"
        )
        
        post_stats = await tortoise.execute_query(
            "SELECT COUNT(*) as total_posts, "
            "COUNT(CASE WHEN published = 1 THEN 1 END) as published_posts "
            "FROM posts"
        )
        
        return response.json({
            "users": user_stats[0] if user_stats else {},
            "posts": post_stats[0] if post_stats else {}
        })
    except Exception as e:
        return response.status(500).json({
            "error": "Failed to get statistics",
            "detail": str(e)
        })


if __name__ == "__main__":
    import uvicorn
    
    print("Starting Nexios Tortoise ORM Example API...")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("Users API: http://localhost:8000/users")
    print("Posts API: http://localhost:8000/posts")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)