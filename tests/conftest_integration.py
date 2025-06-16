"""
Configuration and fixtures for integration tests.
"""

import pytest
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from ticktick_mcp.src.server import initialize_client


@pytest.fixture(scope="session")
def integration_event_loop():
    """Create an event loop for integration tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def check_credentials():
    """Check if TickTick credentials are available for integration tests."""
    load_dotenv()
    
    has_credentials = (
        os.getenv("TICKTICK_ACCESS_TOKEN") is not None and
        os.getenv("TICKTICK_CLIENT_ID") is not None and
        os.getenv("TICKTICK_CLIENT_SECRET") is not None
    )
    
    if has_credentials:
        # Try to initialize the client
        success = initialize_client()
        return success
    
    return False


@pytest.fixture(scope="session")
def test_project_data():
    """Provide test project data for integration tests."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return {
        "name": f"MCP Integration Test Project {timestamp}",
        "color": "#FF6B6B",
        "view_mode": "list"
    }


@pytest.fixture(scope="session")
def test_task_data():
    """Provide test task data for integration tests."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return {
        "title": f"MCP Integration Test Task {timestamp}",
        "content": "This task was created by MCP integration tests",
        "priority": 3  # Medium priority
    }


@pytest.fixture
def skip_if_no_credentials(check_credentials):
    """Skip test if no valid TickTick credentials are available."""
    if not check_credentials:
        pytest.skip(
            "TickTick credentials not available or invalid. "
            "Run 'uv run -m ticktick_mcp.cli auth' to set up authentication."
        )


@pytest.fixture
def integration_cleanup():
    """Fixture to help with test cleanup."""
    created_items = {
        'projects': [],
        'tasks': []
    }
    
    yield created_items
    
    # Cleanup logic could be added here if needed
    # For now, individual tests handle their own cleanup