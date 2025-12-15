import pytest
import strawberry
from nexios.application import NexiosApp
from nexios.testclient import TestClient
from nexios_contrib.graphql import GraphQL
from typing import Optional

@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"
    
    @strawberry.field
    def get_user_agent(self, info: strawberry.Info) -> str:
        """Get user agent from request context."""
        request = info.context["request"]
        return request.headers.get("user-agent", "Unknown")
    
    @strawberry.field
    def get_request_method(self, info: strawberry.Info) -> str:
        """Get request method from context."""
        request = info.context["request"]
        return request.method

schema = strawberry.Schema(query=Query)

def test_graphql_query():
    app = NexiosApp()
    GraphQL(app, schema)
    client = TestClient(app)

    response = client.post(
        "/graphql",
        json={
            "query": "{ hello }"
        }
    )
    
    assert response.status_code == 200
    assert response.json() == {"data": {"hello": "Hello World"}}

def test_graphql_context_user_agent():
    """Test accessing request headers through context."""
    app = NexiosApp()
    GraphQL(app, schema)
    client = TestClient(app)

    response = client.post(
        "/graphql",
        json={
            "query": "{ getUserAgent }"
        },
        headers={"User-Agent": "TestAgent/1.0"}
    )
    
    assert response.status_code == 200
    assert response.json() == {"data": {"getUserAgent": "TestAgent/1.0"}}

def test_graphql_context_request_method():
    """Test accessing request method through context."""
    app = NexiosApp()
    GraphQL(app, schema)
    client = TestClient(app)

    response = client.post(
        "/graphql",
        json={
            "query": "{ getRequestMethod }"
        }
    )
    
    assert response.status_code == 200
    assert response.json() == {"data": {"getRequestMethod": "POST"}}

def test_graphiql_html():
    app = NexiosApp()
    GraphQL(app, schema, graphiql=True)
    client = TestClient(app)

    response = client.get("/graphql")
    
    assert response.status_code == 200
    assert "<!doctype html>" in response.text
    assert "GraphiQL" in response.text
