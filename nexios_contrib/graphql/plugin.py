import json
from typing import Optional, Any, Callable

import strawberry
from strawberry.types import ExecutionResult

from nexios.application import NexiosApp
from nexios.http import Request, Response
from nexios.routing import Route
from nexios.utils.async_helpers import is_async_callable


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
        context_getter: Optional[Callable[[Request, Response], Any]] = None,
    ):
        self.app = app
        self.schema = schema
        self.path = path
        self.graphiql = graphiql
        self.context_getter = context_getter
        
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

            context = {"request": req, "response": res, "req": req}
            if self.context_getter:
                if is_async_callable(self.context_getter):
                    custom_context = await self.context_getter(req, res)
                else:
                    custom_context = self.context_getter(req, res)
                
                # If custom_context is a dict, merge it
                if isinstance(custom_context, dict):
                    context.update(custom_context)
                else:
                    # If it's an object, we use it as the base context and inject req/res/req
                    context = custom_context
                    try:
                         setattr(context, "request", req)
                         setattr(context, "response", res)
                         setattr(context, "req", req)
                    except (AttributeError, TypeError):
                         # If it's not possible to set attributes (e.g. frozen dataclass), 
                         # we might have issues, but we tried.
                         pass

            # Final check to ensure request/response/req are always there if context is a dict
            if isinstance(context, dict):
                context["request"] = req
                context["response"] = res
                context["req"] = req

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
<!doctype html>
<html>
  <head>
    <title>Strawberry GraphiQL</title>
    <link
      rel="icon"
      href="data:image/svg+xml,
        <svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22>
            <!-- Strawberry Emoji as a HTML Entity (hex)  -->
            <text y=%22.9em%22 font-size=%2280%22>&#x1f353;</text>
        </svg>"
    />
    <style>
      body {
        height: 100%;
        margin: 0;
        width: 100%;
        overflow: hidden;
      }

      #graphiql {
        height: 100vh;
        display: flex;
      }

      .docExplorerHide {
        display: none;
      }

      .doc-explorer-contents {
        overflow-y: hidden !important;
      }

      .docExplorerWrap {
        width: unset !important;
        min-width: unset !important;
      }

      .graphiql-explorer-actions select {
        margin-left: 4px;
      }
    </style>

    <script
      crossorigin
      src="https://unpkg.com/react@18.2.0/umd/react.production.min.js"
      integrity="sha384-tMH8h3BGESGckSAVGZ82T9n90ztNXxvdwvdM6UoR56cYcf+0iGXBliJ29D+wZ/x8"
    ></script>
    <script
      crossorigin
      src="https://unpkg.com/react-dom@18.2.0/umd/react-dom.production.min.js"
      integrity="sha384-bm7MnzvK++ykSwVJ2tynSE5TRdN+xL418osEVF2DE/L/gfWHj91J2Sphe582B1Bh"
    ></script>

    <script
      crossorigin
      src="https://unpkg.com/js-cookie@3.0.5/dist/js.cookie.min.js"
      integrity="sha384-/vxhYfM1LENRhdpZ8dwEsQn/X4VhpbEZSiU4m/FwR+PVpzar4fkEOw8FP9Y+OfQN"
    ></script>

    <link
      crossorigin
      rel="stylesheet"
      href="https://unpkg.com/graphiql@3.8.3/graphiql.min.css"
      integrity="sha384-Mq3vbRBY71jfjQAt/DcjxUIYY33ksal4cgdRt9U/hNPvHBCaT2JfJ/PTRiPKf0aM"
    />

    <link
      crossorigin
      rel="stylesheet"
      href="https://unpkg.com/@graphiql/plugin-explorer@1.0.2/dist/style.css"
      integrity="sha384-5DFJlDPW2tSATRbM8kzoP1j194jexLswuNmClWoRr2Q0x7R68JIQzPHZ02Faktwi"
    />
  </head>

  <body>
    <div id="graphiql" class="graphiql-container">Loading...</div>
    <script
      crossorigin
      src="https://unpkg.com/graphiql@3.8.3/graphiql.min.js"
      integrity="sha384-HbRVEFG0JGJZeAHCJ9Xm2+tpknBQ7QZmNlO/DgZtkZ0aJSypT96YYGRNod99l9Ie"
    ></script>
    <script
      crossorigin
      src="https://unpkg.com/@graphiql/plugin-explorer@1.0.2/dist/index.umd.js"
      integrity="sha384-2oonKe47vfHIZnmB6ZZ10vl7T0Y+qrHQF2cmNTaFDuPshpKqpUMGMc9jgj9MLDZ9"
    ></script>
    <script>
      const EXAMPLE_QUERY = `# Welcome to GraphiQL 🍓
#
# GraphiQL is an in-browser tool for writing, validating, and
# testing GraphQL queries.
#
# Type queries into this side of the screen, and you will see intelligent
# typeaheads aware of the current GraphQL type schema and live syntax and
# validation errors highlighted within the text.
#
# GraphQL queries typically start with a "{" character. Lines that starts
# with a # are ignored.
#
# An example GraphQL query might look like:
#
#     {
#       field(arg: "value") {
#         subField
#       }
#     }
#
# Keyboard shortcuts:
#
#       Run Query:  Ctrl-Enter (or press the play button above)
#
#   Auto Complete:  Ctrl-Space (or just start typing)
#
`;

      const fetchURL = window.location.href;

      function httpUrlToWebSockeUrl(url) {
        const parsedURL = new URL(url);
        const protocol = parsedURL.protocol === "http:" ? "ws:" : "wss:";
        parsedURL.protocol = protocol;
        parsedURL.hash = "";
        return parsedURL.toString();
      }

      const headers = {};
      const csrfToken = Cookies.get("csrftoken");

      if (csrfToken) {
        headers["x-csrftoken"] = csrfToken;
      }

      const subscriptionUrl = httpUrlToWebSockeUrl(fetchURL);

      const fetcher = GraphiQL.createFetcher({
        url: fetchURL,
        headers: headers,
        subscriptionUrl,
      });

      const explorerPlugin = GraphiQLPluginExplorer.explorerPlugin();

      const root = ReactDOM.createRoot(document.getElementById("graphiql"));

      root.render(
        React.createElement(GraphiQL, {
          fetcher: fetcher,
          defaultEditorToolsVisibility: true,
          plugins: [explorerPlugin],
          inputValueDeprecation: true,
        }),
      );
    </script>
  </body>
</html>
"""
