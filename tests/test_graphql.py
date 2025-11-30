import pytest
import strawberry
from nexios.application import NexiosApp
from nexios.testclient import TestClient
from nexios_contrib.graphql import GraphQL

@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"

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

def test_graphiql_html():
    app = NexiosApp()
    GraphQL(app, schema, graphiql=True)
    client = TestClient(app)

    response = client.get("/graphql")
    
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    assert "GraphiQL" in response.text
