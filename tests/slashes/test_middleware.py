"""
Integration tests for SlashesMiddleware.
"""
import pytest
from httpx import Response as HttpxResponse

from nexios_contrib.slashes.middleware import SlashesMiddleware, SlashAction


@pytest.mark.asyncio
async def test_remove_trailing_slash_redirect(app_factory, test_client_factory):
    """Test that trailing slashes are removed with REDIRECT_REMOVE action."""
    app = app_factory(middleware=SlashesMiddleware(slash_action=SlashAction.REDIRECT_REMOVE))
    
    @app.get("/test")
    async def test_endpoint(request,response):
        return {"message": "success"}
    
    client = test_client_factory(app,follow_redirects=False)
    response = client.get("/test/")
    
    assert response.status_code == 301
    assert response.headers["location"] == "http://testserver/test"


@pytest.mark.asyncio
async def test_add_trailing_slash_redirect(app_factory, test_client_factory):
    """Test that missing trailing slashes are added with REDIRECT_ADD action."""
    app = app_factory(middleware=SlashesMiddleware(slash_action=SlashAction.REDIRECT_ADD))
    
    @app.get("/test/")
    async def test_endpoint(request,response):
        return {"message": "success"}
    
    client = test_client_factory(app)
    response =  client.get("/test", follow_redirects=False)
    
    assert response.status_code == 301
    assert response.headers["location"] == "http://testserver/test/"


@pytest.mark.asyncio
async def test_remove_trailing_slash_inplace(app_factory, test_client_factory):
    """Test that trailing slashes are removed in-place with REMOVE action."""
    app = app_factory(middleware=SlashesMiddleware(slash_action=SlashAction.REMOVE))
    
    @app.get("/test")
    async def test_endpoint(request,response):
        return {"message": "success"}
    
    client = test_client_factory(app)
    response = client.get("/test/")
    
    assert response.status_code == 200
    assert response.json() == {"message": "success"}


@pytest.mark.asyncio
async def test_add_trailing_slash_inplace(app_factory, test_client_factory):
    """Test that trailing slashes are added in-place with ADD action."""
    app = app_factory(middleware=SlashesMiddleware(slash_action=SlashAction.ADD))
    
    @app.get("/test/")
    async def test_endpoint(request,response):
        return {"message": "success"}
    
    client = test_client_factory(app)
    response = client.get("/test")
    
    assert response.status_code == 200
    assert response.json() == {"message": "success"}


@pytest.mark.asyncio
async def test_double_slash_removal(app_factory, test_client_factory):
    """Test that double slashes are removed from URLs."""
    app = app_factory(middleware=SlashesMiddleware(slash_action=SlashAction.IGNORE))
    
    @app.get("/test/path")
    async def test_endpoint(request,response):
        return {"message": "success"}
    
    client = test_client_factory(app)
    response =  client.get("/test//path")
    
    assert response.status_code == 200
    assert response.json() == {"message": "success"}




@pytest.mark.asyncio
async def test_skip_processing_for_query_params(app_factory, test_client_factory):
    """Test that URLs with query parameters are handled correctly."""
    app = app_factory(middleware=SlashesMiddleware(slash_action=SlashAction.REDIRECT_REMOVE))
    
    @app.get("/search")
    async def search_endpoint(request, response):
        q = request.query_params.get("q")
        return {"query": q}
    
    client = test_client_factory(app)
    response =  client.get("/search/?q=test", follow_redirects=False)
    
    # Should redirect to remove the trailing slash before the query
    assert response.status_code == 301
    assert response.headers["location"] == "http://testserver/search?q=test"


@pytest.mark.asyncio
async def test_custom_redirect_status_code(app_factory, test_client_factory):
    """Test that custom redirect status codes work."""
    app = app_factory(middleware=SlashesMiddleware(
        slash_action=SlashAction.REDIRECT_REMOVE,
        redirect_status_code=308  # Permanent Redirect
    ))
    
    @app.get("/test")
    async def test_endpoint(request, response):
        return {"message": "success"}
    
    client = test_client_factory(app)
    response = client.get("/test/", follow_redirects=False)
    
    assert response.status_code == 308
    assert response.headers["location"] == "http://testserver/test"


@pytest.mark.asyncio
async def test_root_path_handling(app_factory, test_client_factory):
    """Test that root path is handled correctly."""
    app = app_factory(middleware=SlashesMiddleware(slash_action=SlashAction.IGNORE))
    
    @app.get("/")
    async def root_endpoint(request, response):
        return {"message": "root"}
    
    client = test_client_factory(app)
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"message": "root"}
    
    # Root with trailing slash should also work
    response = client.get("//")
    assert response.status_code == 200
    assert response.json() == {"message": "root"}
