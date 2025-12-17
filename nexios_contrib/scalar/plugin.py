"""
Scalar DOC plugin for Nexios - Beautiful OpenAPI documentation using Scalar.
"""

from typing import Optional, Dict, Any, Union
from nexios.application import NexiosApp
from nexios.http import Request, Response
from nexios.routing import Route

try:
    from scalar_doc import ScalarDoc, ScalarConfiguration, ScalarTheme, ScalarHeader, ScalarColorSchema
except ImportError:
    raise ImportError(
        "scalar_doc is required for the Scalar plugin. "
        "Install it with: pip install scalar_doc"
    )


class Scalar:
    """
    Scalar DOC plugin for Nexios.
    
    Provides beautiful, interactive OpenAPI documentation using Scalar.
    """
    
    def __init__(
        self,
        app: NexiosApp,
        path: str = "/scalar-docs",
        openapi_url: str = "/openapi.json",
        title: Optional[str] = None,
        configuration: Optional[ScalarConfiguration] = None,
        theme: Optional[ScalarTheme] = None,
        header: Optional[ScalarHeader] = None,
        custom_spec: Optional[Union[str, Dict[str, Any]]] = None,
        spec_mode: str = "url",  # "url", "json", or "dict"
    ):
        """
        Initialize Scalar documentation.
        
        Args:
            app: NexiosApp instance
            path: URL path for the documentation
            openapi_url: URL path for the OpenAPI spec
            title: Custom title for the documentation
            configuration: Scalar configuration options
            theme: Theme configuration
            header: Header configuration
            custom_spec: Custom OpenAPI spec (optional)
            spec_mode: Mode for custom spec ("url", "json", or "dict")
        """
        self.app = app
        self.path = path
        self.openapi_url = openapi_url
        self.title = title or f"{app.title or 'Nexios API'} Documentation"
        self.configuration = configuration
        self.theme = theme
        self.header = header
        self.custom_spec = custom_spec
        self.spec_mode = spec_mode
        
        self._setup()
    
    def _setup(self):
        """Register the Scalar documentation route."""
        self.app.add_route(
            Route(self.path, self.handle_request, methods=["GET"])
        )
    
    async def handle_request(self, req: Request, res: Response):
        """Handle Scalar documentation requests."""
        return res.html(self._generate_html())
    
    def _generate_html(self) -> str:
        """Generate the Scalar HTML documentation using scalar_doc."""
        # Determine the OpenAPI spec source
        if self.custom_spec:
            if self.spec_mode == "url":
                spec = self.custom_spec
            elif self.spec_mode == "json":
                spec = self.custom_spec
            elif self.spec_mode == "dict":
                spec = self.custom_spec
            else:
                raise ValueError(f"Invalid spec_mode: {self.spec_mode}")
            docs = ScalarDoc.from_spec(spec=spec, mode=self.spec_mode)
        else:
            # Use the app's OpenAPI URL
            docs = ScalarDoc.from_spec(spec=self.openapi_url, mode="url")
        
        # Set title
        docs.set_title(self.title)
        
        # Set configuration if provided
        if self.configuration:
            docs.set_configuration(self.configuration)
        
        # Set theme if provided
        if self.theme:
            docs.set_theme(self.theme)
        
        # Set header if provided
        if self.header:
            docs.set_header(self.header)
        
        # Generate HTML using scalar_doc
        return docs.to_html()
    
    @classmethod
    def from_spec(
        cls,
        app: NexiosApp,
        spec: Union[str, Dict[str, Any]],
        mode: str = "url",
        **kwargs
    ):
        """
        Create Scalar instance from a custom OpenAPI spec.
        
        Args:
            app: NexiosApp instance
            spec: OpenAPI spec (URL, JSON string, or dict)
            mode: Mode for the spec ("url", "json", or "dict")
            **kwargs: Additional arguments for Scalar constructor
        """
        return cls(
            app=app,
            custom_spec=spec,
            spec_mode=mode,
            **kwargs
        )
