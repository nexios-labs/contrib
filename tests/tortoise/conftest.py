"""
Test configuration and fixtures for Tortoise ORM tests.
"""

import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def reset_tortoise_client():
    """Reset the global Tortoise client before each test."""
    # Reset the global client to ensure clean state
    import nexios_contrib.tortoise
    nexios_contrib.tortoise._tortoise_client = None
    yield
    # Clean up after test
    nexios_contrib.tortoise._tortoise_client = None