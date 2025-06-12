"""
Pytest configuration and shared fixtures.
"""

import pytest
import asyncio
from unittest.mock import patch


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_load_dotenv():
    """Mock load_dotenv to prevent loading actual .env file during tests."""
    with patch('dotenv.load_dotenv'):
        yield


@pytest.fixture
def mock_ticktick_global():
    """Mock the global ticktick client in server module."""
    with patch('ticktick_mcp.src.server.ticktick') as mock_client:
        # Ensure the mock client is properly initialized
        mock_client.get_projects.return_value = []
        mock_client.get_project.return_value = {}
        mock_client.get_project_with_data.return_value = {"project": {}, "tasks": []}
        mock_client.get_task.return_value = {}
        mock_client.create_task.return_value = {}
        mock_client.update_task.return_value = {}
        mock_client.complete_task.return_value = {}
        mock_client.delete_task.return_value = {}
        mock_client.create_project.return_value = {}
        mock_client.delete_project.return_value = {}
        yield mock_client