"""
Tests for Scalar documentation plugin.
These tests are designed to run only on Python 3.12+ due to scalar_docs compatibility.
"""
import sys
import pytest
from unittest.mock import Mock, patch
from nexios import NexiosApp
from nexios.http import Request, Response

# Skip scalar tests on Python versions < 3.12
pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason="Scalar tests require Python 3.12+"
)

try:
    from scalar_doc import ScalarConfiguration, ScalarTheme, ScalarHeader, ScalarColorSchema
    SCALAR_AVAILABLE = True
except ImportError:
    SCALAR_AVAILABLE = False

pytest.importorskip("scalar_doc", reason="scalar_doc not available")


class TestScalarPlugin:
    """Test cases for Scalar documentation plugin."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = NexiosApp()
        self.app.title = "Test API"
    
    @pytest.mark.skipif(not SCALAR_AVAILABLE, reason="scalar_doc not available")
    def test_scalar_initialization_defaults(self):
        """Test Scalar plugin initialization with default parameters."""
        from nexios_contrib.scalar import Scalar
        
        scalar = Scalar(self.app)
        
        assert scalar.app == self.app
        assert scalar.path == "/scalar-docs"
        assert scalar.openapi_url == "/openapi.json"
        assert scalar.title == "Test API Documentation"
        assert scalar.configuration is None
        assert scalar.theme is None
        assert scalar.header is None
        assert scalar.custom_spec is None
        assert scalar.spec_mode == "url"
    
    @pytest.mark.skipif(not SCALAR_AVAILABLE, reason="scalar_doc not available")
    def test_scalar_initialization_custom_params(self):
        """Test Scalar plugin initialization with custom parameters."""
        from nexios_contrib.scalar import Scalar, ScalarConfiguration
        
        config = ScalarConfiguration()
        scalar = Scalar(
            app=self.app,
            path="/docs",
            openapi_url="/api/openapi.json",
            title="Custom Docs",
            configuration=config,
            theme=ScalarTheme.DARK,
            header=ScalarHeader()
        )
        
        assert scalar.path == "/docs"
        assert scalar.openapi_url == "/api/openapi.json"
        assert scalar.title == "Custom Docs"
        assert scalar.configuration == config
        assert scalar.theme == ScalarTheme.DARK
        assert scalar.header is not None
    
    @pytest.mark.skipif(not SCALAR_AVAILABLE, reason="scalar_doc not available")
    def test_scalar_from_spec_url(self):
        """Test creating Scalar from custom spec URL."""
        from nexios_contrib.scalar import Scalar
        
        scalar = Scalar.from_spec(
            app=self.app,
            spec="https://api.example.com/openapi.json",
            mode="url",
            path="/custom-docs"
        )
        
        assert scalar.custom_spec == "https://api.example.com/openapi.json"
        assert scalar.spec_mode == "url"
        assert scalar.path == "/custom-docs"
    
    @pytest.mark.skipif(not SCALAR_AVAILABLE, reason="scalar_doc not available")
    def test_scalar_from_spec_dict(self):
        """Test creating Scalar from custom spec dict."""
        from nexios_contrib.scalar import Scalar
        
        spec_dict = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {}
        }
        
        scalar = Scalar.from_spec(
            app=self.app,
            spec=spec_dict,
            mode="dict"
        )
        
        assert scalar.custom_spec == spec_dict
        assert scalar.spec_mode == "dict"
    
    @pytest.mark.skipif(not SCALAR_AVAILABLE, reason="scalar_doc not available")
    def test_scalar_route_registration(self):
        """Test that Scalar properly registers the documentation route."""
        from nexios_contrib.scalar import Scalar
        
        initial_route_count = len(self.app.routes)
        scalar = Scalar(self.app, path="/test-docs")
        
        # Should have added one new route
        assert len(self.app.routes) == initial_route_count + 1
        
        # Check that the route was added with correct path
        route_paths = [route.path for route in self.app.routes]
        assert "/test-docs" in route_paths
    
    @pytest.mark.skipif(not SCALAR_AVAILABLE, reason="scalar_doc not available")
    @patch('nexios_contrib.scalar.plugin.ScalarDoc')
    def test_scalar_handle_request(self, mock_scalar_doc):
        """Test Scalar request handling."""
        from nexios_contrib.scalar import Scalar
        
        # Mock the ScalarDoc instance
        mock_docs = Mock()
        mock_docs.to_html.return_value = "<html><body>Test Docs</body></html>"
        mock_scalar_doc.from_spec.return_value = mock_docs
        
        scalar = Scalar(self.app)
        
        # Create mock request and response
        request = Mock(spec=Request)
        response = Mock(spec=Response)
        response.html = Mock()
        
        # Handle the request
        result = await scalar.handle_request(request, response)
        
        # Verify HTML was set
        response.html.assert_called_once_with("<html><body>Test Docs</body></html>")
    
    @pytest.mark.skipif(not SCALAR_AVAILABLE, reason="scalar_doc not available")
    def test_scalar_invalid_spec_mode(self):
        """Test Scalar with invalid spec mode raises error."""
        from nexios_contrib.scalar import Scalar
        
        with pytest.raises(ValueError, match="Invalid spec_mode"):
            Scalar.from_spec(
                app=self.app,
                spec={"test": "spec"},
                mode="invalid_mode"
            )
    
    @pytest.mark.skipif(not SCALAR_AVAILABLE, reason="scalar_doc not available")
    def test_scalar_import_error_handling(self):
        """Test that Scalar raises ImportError when scalar_doc is not available."""
        with patch.dict('sys.modules', {'scalar_doc': None}):
            # Remove the module from cache
            if 'scalar_doc' in sys.modules:
                del sys.modules['scalar_doc']
            
            # Re-import to trigger ImportError
            import importlib
            from nexios_contrib.scalar import plugin
            importlib.reload(plugin)
            
            with pytest.raises(ImportError, match="scalar_doc is required"):
                plugin.Scalar(self.app)


class TestScalarIntegration:
    """Integration tests for Scalar plugin."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = NexiosApp()
        self.app.title = "Integration Test API"
    
    @pytest.mark.skipif(not SCALAR_AVAILABLE, reason="scalar_doc not available")
    def test_scalar_with_real_app(self):
        """Test Scalar integration with a real Nexios app."""
        from nexios_contrib.scalar import Scalar
        
        # Add a test route
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        # Initialize Scalar
        scalar = Scalar(self.app, path="/docs")
        
        # Verify the route was added
        route_paths = [route.path for route in self.app.routes]
        assert "/docs" in route_paths
        assert "/test" in route_paths
    
    @pytest.mark.skipif(not SCALAR_AVAILABLE, reason="scalar_doc not available")
    def test_scalar_multiple_instances(self):
        """Test creating multiple Scalar instances."""
        from nexios_contrib.scalar import Scalar
        
        scalar1 = Scalar(self.app, path="/docs1")
        scalar2 = Scalar(self.app, path="/docs2")
        
        # Both should be registered
        route_paths = [route.path for route in self.app.routes]
        assert "/docs1" in route_paths
        assert "/docs2" in route_paths


if __name__ == "__main__":
    pytest.main([__file__])
