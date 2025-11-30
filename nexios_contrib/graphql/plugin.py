import json
from typing import Optional, Any

import strawberry
from strawberry.types import ExecutionResult

from nexios.application import NexiosApp
from nexios.http import Request, Response
from nexios.routing import Route


class GraphQL:
    """
    GraphQL plugin for Nexios using Strawberry.
    """

    def __init__(
        self,
        app: NexiosApp,
        schema: strawberry.Schema,
        path: str = "/graphql",
        graphiql: bool = True,
    ):
        self.app = app
        self.schema = schema
        self.path = path
        self.graphiql = graphiql
        
        self._setup()

    def _setup(self):
        """Register the GraphQL route."""
        self.app.add_route(
            Route(self.path, self.handle_request, methods=["GET", "POST"])
        )

    async def handle_request(self, req: Request, res: Response):
        """Handle GraphQL requests."""
        if req.method == "GET":
            if self.graphiql:
                return res.html(self._get_graphiql_html())
            return res.status(404).text("Not Found")

        if req.method == "POST":
            try:
                data = await req.json
            except Exception:
                return res.status(400).json({"errors": [{"message": "Invalid JSON body"}]})

            if not isinstance(data, dict):
                 return res.status(400).json({"errors": [{"message": "JSON body must be an object"}]})

            query = data.get("query")
            variables = data.get("variables")
            operation_name = data.get("operationName")

            context = {"request": req, "response": res}

            result: ExecutionResult = await self.schema.execute(
                query,
                variable_values=variables,
                context_value=context,
                operation_name=operation_name,
            )

            response_data: dict[str, Any] = {}
            if result.data is not None:
                response_data["data"] = result.data
            if result.errors:
                response_data["errors"] = [err.formatted for err in result.errors]
            
            return res.json(response_data)

    def _get_graphiql_html(self) -> str:
        """Return the GraphiQL HTML."""
        return """
<!DOCTYPE html>
<html>
  <head>
    <style>
      html, body {
        height: 100%;
        margin: 0;
        overflow: hidden;
        width: 100%;
      }
    </style>
    <link href="//unpkg.com/graphiql/graphiql.min.css" rel="stylesheet" />
    <script src="//unpkg.com/react/umd/react.production.min.js"></script>
    <script src="//unpkg.com/react-dom/umd/react-dom.production.min.js"></script>
    <script src="//unpkg.com/graphiql/graphiql.min.js"></script>
  </head>
  <body>
    <div id="graphiql">Loading...</div>
    <script>
      const fetcher = GraphiQL.createFetcher({ url: window.location.href });
      ReactDOM.render(
        React.createElement(GraphiQL, { fetcher: fetcher }),
        document.getElementById('graphiql'),
      );
    </script>
  </body>
</html>
"""
