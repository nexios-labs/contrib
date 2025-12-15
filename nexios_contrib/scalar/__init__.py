"""
Scalar DOC plugin for Nexios - Beautiful OpenAPI documentation using Scalar.
"""

from .plugin import Scalar

# Re-export scalar_doc classes for convenience
try:
    from scalar_doc import ScalarConfiguration, ScalarTheme, ScalarHeader, ScalarColorSchema
    __all__ = ["Scalar", "ScalarConfiguration", "ScalarTheme", "ScalarHeader", "ScalarColorSchema"]
except ImportError:
    __all__ = ["Scalar"]
