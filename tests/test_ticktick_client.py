import pytest
import json
import os
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

import requests

from ticktick_mcp.src.ticktick_client import TickTickClient


class TestTickTickClient:
    """Test suite for TickTickClient."""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables."""
        with patch.dict(os.environ, {
            'TICKTICK_CLIENT_ID': 'test_client_id',
            'TICKTICK_CLIENT_SECRET': 'test_client_secret',
            'TICKTICK_ACCESS_TOKEN': 'test_access_token',
            'TICKTICK_REFRESH_TOKEN': 'test_refresh_token'
        }):
            yield
    
    @pytest.fixture
    def client(self, mock_env_vars):
        """Create TickTickClient instance."""
        with patch('ticktick_mcp.src.ticktick_client.load_dotenv'):
            return TickTickClient()
    
    def test_init_success(self, mock_env_vars):
        """Test successful client initialization."""
        with patch('ticktick_mcp.src.ticktick_client.load_dotenv'):
            client = TickTickClient()
            
            assert client.client_id == 'test_client_id'
            assert client.client_secret == 'test_client_secret'
            assert client.access_token == 'test_access_token'
            assert client.refresh_token == 'test_refresh_token'
            assert client.base_url == "https://api.ticktick.com/open/v1"
            assert client.headers["Authorization"] == "Bearer test_access_token"
    
    def test_init_no_access_token(self):
        """Test client initialization without access token."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('ticktick_mcp.src.ticktick_client.load_dotenv'):
                with pytest.raises(ValueError, match="TICKTICK_ACCESS_TOKEN environment variable is not set"):
                    TickTickClient()
    
    def test_init_custom_base_url(self, mock_env_vars):
        """Test client initialization with custom base URL."""
        with patch.dict(os.environ, {'TICKTICK_BASE_URL': 'https://api.dida365.com/open/v1'}):
            with patch('ticktick_mcp.src.ticktick_client.load_dotenv'):
                client = TickTickClient()
                assert client.base_url == "https://api.dida365.com/open/v1"

    # Test token refresh
    @patch('requests.post')
    def test_refresh_access_token_success(self, mock_post, client):
        """Test successful access token refresh."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token'
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        with patch.object(client, '_save_tokens_to_env') as mock_save:
            result = client._refresh_access_token()
            
            assert result is True
            assert client.access_token == 'new_access_token'
            assert client.refresh_token == 'new_refresh_token'
            assert client.headers["Authorization"] == "Bearer new_access_token"
            mock_save.assert_called_once()
    
    @patch('requests.post')
    def test_refresh_access_token_no_refresh_token(self, mock_post, client):
        """Test token refresh without refresh token."""
        client.refresh_token = None
        
        result = client._refresh_access_token()
        
        assert result is False
        mock_post.assert_not_called()
    
    @patch('requests.post')
    def test_refresh_access_token_network_error(self, mock_post, client):
        """Test token refresh with network error."""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")
        
        result = client._refresh_access_token()
        
        assert result is False

    # Test save tokens to env
    def test_save_tokens_to_env_new_file(self, client):
        """Test saving tokens to new .env file."""
        tokens = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token'
        }
        
        with patch('pathlib.Path.exists', return_value=False):
            with patch('builtins.open', mock_open()) as mock_file:
                client._save_tokens_to_env(tokens)
                
                # Check that file was written with correct content
                mock_file.assert_called_with(Path('.env'), 'w')
                handle = mock_file()
                written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
                assert 'TICKTICK_ACCESS_TOKEN=new_access_token' in written_content
                assert 'TICKTICK_REFRESH_TOKEN=new_refresh_token' in written_content
    
    def test_save_tokens_to_env_existing_file(self, client):
        """Test saving tokens to existing .env file."""
        existing_content = "SOME_OTHER_VAR=value\nTICKTICK_ACCESS_TOKEN=old_token\n"
        tokens = {'access_token': 'new_access_token'}
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=existing_content)) as mock_file:
                client._save_tokens_to_env(tokens)
                
                # Verify the file was read and written
                assert mock_file.call_count == 2  # Once for read, once for write

    # Test API requests
    @patch('requests.get')
    def test_make_request_get_success(self, mock_get, client):
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = client._make_request("GET", "/test")
        
        assert result == {"data": "test"}
        mock_get.assert_called_once_with(
            "https://api.ticktick.com/open/v1/test", 
            headers=client.headers
        )
    
    @patch('requests.post')
    def test_make_request_post_success(self, mock_post, client):
        """Test successful POST request."""
        mock_response = Mock()
        mock_response.json.return_value = {"created": True}
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        test_data = {"name": "test"}
        result = client._make_request("POST", "/test", test_data)
        
        assert result == {"created": True}
        mock_post.assert_called_once_with(
            "https://api.ticktick.com/open/v1/test", 
            headers=client.headers,
            json=test_data
        )
    
    @patch('requests.delete')
    def test_make_request_delete_success(self, mock_delete, client):
        """Test successful DELETE request."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.text = ""
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response
        
        result = client._make_request("DELETE", "/test")
        
        assert result == {}
        mock_delete.assert_called_once_with(
            "https://api.ticktick.com/open/v1/test", 
            headers=client.headers
        )
    
    @patch('requests.get')
    def test_make_request_unauthorized_with_refresh(self, mock_get, client):
        """Test request with 401 error that gets refreshed."""
        # First call returns 401, second call succeeds
        unauthorized_response = Mock()
        unauthorized_response.status_code = 401
        unauthorized_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401")
        
        success_response = Mock()
        success_response.json.return_value = {"data": "success"}
        success_response.status_code = 200
        success_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [unauthorized_response, success_response]
        
        with patch.object(client, '_refresh_access_token', return_value=True):
            result = client._make_request("GET", "/test")
            
            assert result == {"data": "success"}
            assert mock_get.call_count == 2
    
    @patch('requests.get')
    def test_make_request_network_error(self, mock_get, client):
        """Test request with network error."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        result = client._make_request("GET", "/test")
        
        assert result == {"error": "Network error"}
    
    def test_make_request_unsupported_method(self, client):
        """Test request with unsupported HTTP method."""
        with pytest.raises(ValueError, match="Unsupported HTTP method: PATCH"):
            client._make_request("PATCH", "/test")

    # Test project methods
    @patch.object(TickTickClient, '_make_request')
    def test_get_projects(self, mock_request, client):
        """Test get_projects method."""
        mock_request.return_value = [{"id": "1", "name": "Test"}]
        
        result = client.get_projects()
        
        assert result == [{"id": "1", "name": "Test"}]
        mock_request.assert_called_once_with("GET", "/project")
    
    @patch.object(TickTickClient, '_make_request')
    def test_get_project(self, mock_request, client):
        """Test get_project method."""
        mock_request.return_value = {"id": "1", "name": "Test"}
        
        result = client.get_project("project123")
        
        assert result == {"id": "1", "name": "Test"}
        mock_request.assert_called_once_with("GET", "/project/project123")
    
    @patch.object(TickTickClient, '_make_request')
    def test_get_project_with_data(self, mock_request, client):
        """Test get_project_with_data method."""
        mock_request.return_value = {"project": {"id": "1"}, "tasks": []}
        
        result = client.get_project_with_data("project123")
        
        assert result == {"project": {"id": "1"}, "tasks": []}
        mock_request.assert_called_once_with("GET", "/project/project123/data")
    
    @patch.object(TickTickClient, '_make_request')
    def test_create_project(self, mock_request, client):
        """Test create_project method."""
        mock_request.return_value = {"id": "new_project", "name": "New Project"}
        
        result = client.create_project("New Project", "#FF0000", "kanban")
        
        expected_data = {
            "name": "New Project",
            "color": "#FF0000",
            "viewMode": "kanban",
            "kind": "TASK"
        }
        assert result == {"id": "new_project", "name": "New Project"}
        mock_request.assert_called_once_with("POST", "/project", expected_data)
    
    @patch.object(TickTickClient, '_make_request')
    def test_delete_project(self, mock_request, client):
        """Test delete_project method."""
        mock_request.return_value = {}
        
        result = client.delete_project("project123")
        
        assert result == {}
        mock_request.assert_called_once_with("DELETE", "/project/project123")

    # Test task methods
    @patch.object(TickTickClient, '_make_request')
    def test_get_task(self, mock_request, client):
        """Test get_task method."""
        mock_request.return_value = {"id": "task123", "title": "Test Task"}
        
        result = client.get_task("project123", "task123")
        
        assert result == {"id": "task123", "title": "Test Task"}
        mock_request.assert_called_once_with("GET", "/project/project123/task/task123")
    
    @patch.object(TickTickClient, '_make_request')
    def test_create_task(self, mock_request, client):
        """Test create_task method."""
        mock_request.return_value = {"id": "new_task", "title": "New Task"}
        
        result = client.create_task(
            title="New Task",
            project_id="project123",
            content="Task content",
            priority=3,
            start_date="2024-01-01T00:00:00+0000",
            due_date="2024-01-02T00:00:00+0000"
        )
        
        expected_data = {
            "title": "New Task",
            "projectId": "project123",
            "content": "Task content",
            "priority": 3,
            "startDate": "2024-01-01T00:00:00+0000",
            "dueDate": "2024-01-02T00:00:00+0000",
            "isAllDay": False
        }
        assert result == {"id": "new_task", "title": "New Task"}
        mock_request.assert_called_once_with("POST", "/task", expected_data)
    
    @patch.object(TickTickClient, '_make_request')
    def test_create_task_minimal(self, mock_request, client):
        """Test create_task with minimal parameters."""
        mock_request.return_value = {"id": "new_task", "title": "New Task"}
        
        result = client.create_task("New Task", "project123")
        
        expected_data = {
            "title": "New Task",
            "projectId": "project123",
            "priority": 0,
            "isAllDay": False
        }
        assert result == {"id": "new_task", "title": "New Task"}
        mock_request.assert_called_once_with("POST", "/task", expected_data)
    
    @patch.object(TickTickClient, '_make_request')
    def test_update_task(self, mock_request, client):
        """Test update_task method."""
        mock_request.return_value = {"id": "task123", "title": "Updated Task"}
        
        result = client.update_task(
            task_id="task123",
            project_id="project123",
            title="Updated Task",
            priority=5
        )
        
        expected_data = {
            "id": "task123",
            "projectId": "project123",
            "title": "Updated Task",
            "priority": 5
        }
        assert result == {"id": "task123", "title": "Updated Task"}
        mock_request.assert_called_once_with("POST", "/task/task123", expected_data)
    
    @patch.object(TickTickClient, '_make_request')
    def test_complete_task(self, mock_request, client):
        """Test complete_task method."""
        mock_request.return_value = {}
        
        result = client.complete_task("project123", "task123")
        
        assert result == {}
        mock_request.assert_called_once_with("POST", "/project/project123/task/task123/complete")
    
    @patch.object(TickTickClient, '_make_request')
    def test_delete_task(self, mock_request, client):
        """Test delete_task method."""
        mock_request.return_value = {}
        
        result = client.delete_task("project123", "task123")
        
        assert result == {}
        mock_request.assert_called_once_with("DELETE", "/project/project123/task/task123")