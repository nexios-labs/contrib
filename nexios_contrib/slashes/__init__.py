"""
Nexios URL Normalization contrib package.
"""

from .middleware import SlashesMiddleware, SlashAction
from .helpers import (
    add_trailing_slash,
    clean_url_path,
    get_path_segments,
    has_trailing_slash,
    join_path_segments,
    normalize_path,
    normalize_url,
    remove_trailing_slash,
    should_skip_path_processing,
)

__all__ = [
    "SlashesMiddleware",
    "SlashAction",
    "add_trailing_slash",
    "clean_url_path",
    "get_path_segments",
    "has_trailing_slash",
    "join_path_segments",
    "normalize_path",
    "normalize_url",
    "remove_trailing_slash",
    "should_skip_path_processing",
]

def Slashes(
    slash_action: SlashAction = SlashAction.REDIRECT_REMOVE,
    auto_remove_double_slashes: bool = True,
    redirect_status_code: int = 301
) -> SlashesMiddleware:
    """
    Create a SlashesMiddleware instance with the given configuration.

    Args:
        slash_action: How to handle trailing slashes
        auto_remove_double_slashes: Whether to remove double slashes
        redirect_status_code: HTTP status code for redirects

    Returns:
        Configured SlashesMiddleware instance
    """
    return SlashesMiddleware(
        slash_action=slash_action,
        auto_remove_double_slashes=auto_remove_double_slashes,
        redirect_status_code=redirect_status_code
    )
