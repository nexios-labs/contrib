"""
Tests for JsonRpcRegistry functionality.
"""

import pytest

from nexios_contrib.jrpc import JsonRpcRegistry, get_registry
from nexios_contrib.jrpc.exceptions import JsonRpcMethodNotFound


class TestJsonRpcRegistry:
    """Tests for JsonRpcRegistry."""

    def test_registry_singleton(self, registry):
        """Test that registry is a singleton."""
        registry2 = JsonRpcRegistry()
        assert registry is registry2
        assert registry.methods is registry2.methods

    def test_get_registry_function(self):
        """Test get_registry function returns the same instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    def test_register_method_with_default_name(self, registry):
        """Test registering a method with default name."""

        def add(a: int, b: int) -> int:
            return a + b

        # Register the method
        registered_func = registry.register()(add)

        # Should return the same function
        assert registered_func is add

        # Should be registered in the registry
        assert "add" in registry.methods
        assert registry.methods["add"] is add

    def test_register_method_with_custom_name(self, registry):
        """Test registering a method with custom name."""

        def multiply(a: int, b: int) -> int:
            return a * b

        # Register with custom name
        registered_func = registry.register("custom_multiply")(multiply)

        # Should return the same function
        assert registered_func is multiply

        # Should be registered with custom name
        assert "custom_multiply" in registry.methods
        assert registry.methods["custom_multiply"] is multiply

        # Original name should not be registered
        assert "multiply" not in registry.methods

    def test_get_method_success(self, registry):
        """Test getting a registered method."""

        def divide(a: float, b: float) -> float:
            return a / b

        registry.register()(divide)

        # Get the method
        retrieved_method = registry.get_method("divide")
        assert retrieved_method is divide

    def test_get_method_not_found(self, registry):
        """Test getting a non-existent method raises error."""

        with pytest.raises(JsonRpcMethodNotFound) as exc_info:
            registry.get_method("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_multiple_methods_registration(self, registry):
        """Test registering multiple methods."""

        def method1() -> str:
            return "method1"

        def method2() -> str:
            return "method2"

        def method3() -> str:
            return "method3"

        # Register all methods
        registry.register()(method1)
        registry.register()(method2)
        registry.register("custom_method3")(method3)

        # Check all are registered
        assert registry.methods["method1"] is method1
        assert registry.methods["method2"] is method2
        assert registry.methods["custom_method3"] is method3

        # Check total count
        assert len(registry.methods) == 3

    def test_registry_persistence_across_calls(self, registry):
        """Test that registry persists across multiple calls."""

        def first_method() -> str:
            return "first"

        def second_method() -> str:
            return "second"

        # Register first method
        registry.register()(first_method)

        # Create new registry instance (should be same due to singleton)
        registry2 = JsonRpcRegistry()

        # Should still have the first method
        assert "first_method" in registry2.methods

        # Register second method
        registry2.register()(second_method)

        # Both should be available
        assert registry.get_method("first_method") is first_method
        assert registry.get_method("second_method") is second_method

    

    def test_registry_isolation_between_tests(self, registry):
        """Test that registry is clean between tests."""

        # Registry should start empty in each test
        assert len(registry.methods) == 0

        # Register a method
        def test_method() -> str:
            return "test"

        registry.register()(test_method)

        # Should have the method
        assert len(registry.methods) == 1
        assert "test_method" in registry.methods
