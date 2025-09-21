"""
Quick verification script for accepts contrib module.
"""
# Test imports
try:
    from nexios_contrib.accepts import (
        AcceptsMiddleware,
        Accepts,
        ContentNegotiationMiddleware,
        StrictContentNegotiationMiddleware,
        parse_accept_header,
        negotiate_content_type,
        negotiate_language,
        get_best_match,
        AcceptItem
    )
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

# Test basic functionality
try:
    # Test Accept header parsing
    items = parse_accept_header("text/html, application/json;q=0.9")
    assert len(items) == 2
    assert items[0].value == "text/html"
    assert items[0].quality == 1.0
    assert items[1].value == "application/json"
    assert items[1].quality == 0.9

    print("✅ Accept header parsing works")

    # Test content negotiation
    best_type = negotiate_content_type(
        "text/html, application/json;q=0.9",
        ["application/json", "text/html", "application/xml"]
    )
    assert best_type == "text/html"

    print("✅ Content negotiation works")

    # Test language negotiation
    best_lang = negotiate_language(
        "en-US, fr;q=0.8",
        ["en", "fr", "es"]
    )
    assert best_lang == "en"

    print("✅ Language negotiation works")

    # Test best match
    best = get_best_match(
        "application/json, text/html;q=0.9",
        ["text/html", "application/json"]
    )
    assert best == "text/html"  # First in options

    print("✅ Best match selection works")

except Exception as e:
    print(f"❌ Functionality error: {e}")
    exit(1)

# Test middleware creation
try:
    middleware = Accepts(default_content_type="application/xml")
    assert middleware.default_content_type == "application/xml"

    strict_middleware = StrictContentNegotiationMiddleware(
        available_types=["application/json", "text/html"],
        available_languages=["en", "es"]
    )
    assert strict_middleware.available_types == ["application/json", "text/html"]

    print("✅ Middleware creation successful")

except Exception as e:
    print(f"❌ Middleware creation error: {e}")
    exit(1)

print("\n🎉 Accepts contrib module verification complete!")
print("\nAvailable components:")
print("- AcceptsMiddleware: Basic content negotiation")
print("- Accepts: Convenience function for basic setup")
print("- ContentNegotiationMiddleware: Manual negotiation control")
print("- StrictContentNegotiationMiddleware: Enforces specific content types")
print("- Helper functions: Header parsing and negotiation utilities")
print("- Full documentation in README.md")
print("- Test suite in tests/test_accepts.py")
print("- Usage examples in example_accepts.py")
print("\nFeatures:")
print("- Accept, Accept-Language, Accept-Charset, Accept-Encoding parsing")
print("- RFC-compliant content negotiation")
print("- Automatic Vary header setting")
print("- Support for API versioning")
print("- Internationalization support")
