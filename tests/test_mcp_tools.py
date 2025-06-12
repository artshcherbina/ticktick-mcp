import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from ticktick_mcp.src.server import (
    get_projects, get_project, get_project_tasks, get_task,
    create_task, update_task, complete_task, delete_task,
    create_project, delete_project, initialize_client, ticktick
)


class TestMCPTools:
    """Test suite for TickTick MCP tools."""
    
    @pytest.fixture
    def mock_ticktick_client(self):
        """Mock TickTick client fixture."""
        with patch('ticktick_mcp.src.server.ticktick') as mock_client:
            yield mock_client
    
    @pytest.fixture
    def sample_project(self):
        """Sample project data."""
        return {
            "id": "project123",
            "name": "Test Project",
            "color": "#FF0000",
            "viewMode": "list",
            "closed": False,
            "kind": "TASK"
        }
    
    @pytest.fixture
    def sample_task(self):
        """Sample task data."""
        return {
            "id": "task123",
            "title": "Test Task",
            "projectId": "project123",
            "content": "This is a test task",
            "priority": 3,
            "status": 0,
            "startDate": "2024-01-01T00:00:00+0000",
            "dueDate": "2024-01-02T00:00:00+0000",
            "items": [
                {"id": "item1", "title": "Subtask 1", "status": 0},
                {"id": "item2", "title": "Subtask 2", "status": 1}
            ]
        }
    
    @pytest.fixture
    def sample_projects_list(self, sample_project):
        """Sample list of projects."""
        return [
            sample_project,
            {
                "id": "project456", 
                "name": "Another Project",
                "color": "#00FF00",
                "viewMode": "kanban"
            }
        ]

    # Test get_projects
    @pytest.mark.asyncio
    async def test_get_projects_success(self, mock_ticktick_client, sample_projects_list):
        """Test successful project retrieval."""
        mock_ticktick_client.get_projects.return_value = sample_projects_list
        
        result = await get_projects()
        
        assert "Found 2 projects:" in result
        assert "Test Project" in result
        assert "Another Project" in result
        assert "ID: project123" in result
        mock_ticktick_client.get_projects.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_projects_empty(self, mock_ticktick_client):
        """Test empty projects list."""
        mock_ticktick_client.get_projects.return_value = []
        
        result = await get_projects()
        
        assert result == "No projects found."
        mock_ticktick_client.get_projects.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_projects_error(self, mock_ticktick_client):
        """Test projects retrieval error."""
        mock_ticktick_client.get_projects.return_value = {"error": "API Error"}
        
        result = await get_projects()
        
        assert "Error fetching projects: API Error" in result
    
    @pytest.mark.asyncio
    async def test_get_projects_client_not_initialized(self):
        """Test get_projects when client is not initialized."""
        with patch('ticktick_mcp.src.server.ticktick', None):
            with patch('ticktick_mcp.src.server.initialize_client', return_value=False):
                result = await get_projects()
                assert "Failed to initialize TickTick client" in result

    # Test get_project
    @pytest.mark.asyncio
    async def test_get_project_success(self, mock_ticktick_client, sample_project):
        """Test successful single project retrieval."""
        mock_ticktick_client.get_project.return_value = sample_project
        
        result = await get_project("project123")
        
        assert "Name: Test Project" in result
        assert "ID: project123" in result
        assert "Color: #FF0000" in result
        mock_ticktick_client.get_project.assert_called_once_with("project123")
    
    @pytest.mark.asyncio
    async def test_get_project_error(self, mock_ticktick_client):
        """Test project retrieval error."""
        mock_ticktick_client.get_project.return_value = {"error": "Project not found"}
        
        result = await get_project("invalid_id")
        
        assert "Error fetching project: Project not found" in result

    # Test get_project_tasks
    @pytest.mark.asyncio
    async def test_get_project_tasks_success(self, mock_ticktick_client, sample_task, sample_project):
        """Test successful project tasks retrieval."""
        project_data = {
            "project": sample_project,
            "tasks": [sample_task]
        }
        mock_ticktick_client.get_project_with_data.return_value = project_data
        
        result = await get_project_tasks("project123")
        
        assert "Found 1 tasks in project 'Test Project'" in result
        assert "Test Task" in result
        assert "Priority: Medium" in result
        assert "Subtasks (2):" in result
        mock_ticktick_client.get_project_with_data.assert_called_once_with("project123")
    
    @pytest.mark.asyncio
    async def test_get_project_tasks_empty(self, mock_ticktick_client, sample_project):
        """Test project with no tasks."""
        project_data = {
            "project": sample_project,
            "tasks": []
        }
        mock_ticktick_client.get_project_with_data.return_value = project_data
        
        result = await get_project_tasks("project123")
        
        assert "No tasks found in project 'Test Project'" in result

    # Test get_task
    @pytest.mark.asyncio
    async def test_get_task_success(self, mock_ticktick_client, sample_task):
        """Test successful task retrieval."""
        mock_ticktick_client.get_task.return_value = sample_task
        
        result = await get_task("project123", "task123")
        
        assert "Title: Test Task" in result
        assert "ID: task123" in result
        assert "Priority: Medium" in result
        assert "Status: Active" in result
        mock_ticktick_client.get_task.assert_called_once_with("project123", "task123")

    # Test create_task
    @pytest.mark.asyncio
    async def test_create_task_success(self, mock_ticktick_client, sample_task):
        """Test successful task creation."""
        mock_ticktick_client.create_task.return_value = sample_task
        
        result = await create_task(
            title="New Task",
            project_id="project123",
            content="Task content",
            priority=3
        )
        
        assert "Task created successfully:" in result
        assert "Test Task" in result
        mock_ticktick_client.create_task.assert_called_once_with(
            title="New Task",
            project_id="project123",
            content="Task content",
            start_date=None,
            due_date=None,
            priority=3
        )
    
    @pytest.mark.asyncio
    async def test_create_task_invalid_priority(self, mock_ticktick_client):
        """Test task creation with invalid priority."""
        result = await create_task(
            title="New Task",
            project_id="project123",
            priority=10  # Invalid priority
        )
        
        assert "Invalid priority" in result
        mock_ticktick_client.create_task.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_task_invalid_date(self, mock_ticktick_client):
        """Test task creation with invalid date format."""
        result = await create_task(
            title="New Task",
            project_id="project123",
            start_date="invalid-date"
        )
        
        assert "Invalid start_date format" in result
        mock_ticktick_client.create_task.assert_not_called()

    # Test update_task
    @pytest.mark.asyncio
    async def test_update_task_success(self, mock_ticktick_client, sample_task):
        """Test successful task update."""
        updated_task = sample_task.copy()
        updated_task["title"] = "Updated Task"
        mock_ticktick_client.update_task.return_value = updated_task
        
        result = await update_task(
            task_id="task123",
            project_id="project123",
            title="Updated Task"
        )
        
        assert "Task updated successfully:" in result
        mock_ticktick_client.update_task.assert_called_once_with(
            task_id="task123",
            project_id="project123",
            title="Updated Task",
            content=None,
            start_date=None,
            due_date=None,
            priority=None
        )

    # Test complete_task
    @pytest.mark.asyncio
    async def test_complete_task_success(self, mock_ticktick_client):
        """Test successful task completion."""
        mock_ticktick_client.complete_task.return_value = {}
        
        result = await complete_task("project123", "task123")
        
        assert "Task task123 marked as complete" in result
        mock_ticktick_client.complete_task.assert_called_once_with("project123", "task123")
    
    @pytest.mark.asyncio
    async def test_complete_task_error(self, mock_ticktick_client):
        """Test task completion error."""
        mock_ticktick_client.complete_task.return_value = {"error": "Task not found"}
        
        result = await complete_task("project123", "invalid_task")
        
        assert "Error completing task: Task not found" in result

    # Test delete_task
    @pytest.mark.asyncio
    async def test_delete_task_success(self, mock_ticktick_client):
        """Test successful task deletion."""
        mock_ticktick_client.delete_task.return_value = {}
        
        result = await delete_task("project123", "task123")
        
        assert "Task task123 deleted successfully" in result
        mock_ticktick_client.delete_task.assert_called_once_with("project123", "task123")

    # Test create_project
    @pytest.mark.asyncio
    async def test_create_project_success(self, mock_ticktick_client, sample_project):
        """Test successful project creation."""
        mock_ticktick_client.create_project.return_value = sample_project
        
        result = await create_project(
            name="New Project",
            color="#0000FF",
            view_mode="kanban"
        )
        
        assert "Project created successfully:" in result
        assert "Test Project" in result
        mock_ticktick_client.create_project.assert_called_once_with(
            name="New Project",
            color="#0000FF",
            view_mode="kanban"
        )
    
    @pytest.mark.asyncio
    async def test_create_project_invalid_view_mode(self, mock_ticktick_client):
        """Test project creation with invalid view mode."""
        result = await create_project(
            name="New Project",
            view_mode="invalid_mode"
        )
        
        assert "Invalid view_mode" in result
        mock_ticktick_client.create_project.assert_not_called()

    # Test delete_project
    @pytest.mark.asyncio
    async def test_delete_project_success(self, mock_ticktick_client):
        """Test successful project deletion."""
        mock_ticktick_client.delete_project.return_value = {}
        
        result = await delete_project("project123")
        
        assert "Project project123 deleted successfully" in result
        mock_ticktick_client.delete_project.assert_called_once_with("project123")

    # Test exception handling
    @pytest.mark.asyncio
    async def test_get_projects_exception(self, mock_ticktick_client):
        """Test get_projects with exception."""
        mock_ticktick_client.get_projects.side_effect = Exception("Network error")
        
        result = await get_projects()
        
        assert "Error retrieving projects: Network error" in result
    
    @pytest.mark.asyncio
    async def test_create_task_exception(self, mock_ticktick_client):
        """Test create_task with exception."""
        mock_ticktick_client.create_task.side_effect = Exception("API error")
        
        result = await create_task("Test Task", "project123")
        
        assert "Error creating task: API error" in result


class TestClientInitialization:
    """Test client initialization."""
    
    @patch('ticktick_mcp.src.server.os.getenv')
    @patch('ticktick_mcp.src.server.TickTickClient')
    def test_initialize_client_success(self, mock_client_class, mock_getenv):
        """Test successful client initialization."""
        mock_getenv.return_value = "test_token"
        mock_client = Mock()
        mock_client.get_projects.return_value = [{"id": "1", "name": "Test"}]
        mock_client_class.return_value = mock_client
        
        with patch('ticktick_mcp.src.server.load_dotenv'):
            result = initialize_client()
        
        assert result is True
        mock_client_class.assert_called_once()
    
    @patch('ticktick_mcp.src.server.os.getenv')
    def test_initialize_client_no_token(self, mock_getenv):
        """Test client initialization without access token."""
        mock_getenv.return_value = None
        
        with patch('ticktick_mcp.src.server.load_dotenv'):
            result = initialize_client()
        
        assert result is False
    
    @patch('ticktick_mcp.src.server.os.getenv')
    @patch('ticktick_mcp.src.server.TickTickClient')
    def test_initialize_client_api_error(self, mock_client_class, mock_getenv):
        """Test client initialization with API error."""
        mock_getenv.return_value = "test_token"
        mock_client = Mock()
        mock_client.get_projects.return_value = {"error": "Unauthorized"}
        mock_client_class.return_value = mock_client
        
        with patch('ticktick_mcp.src.server.load_dotenv'):
            result = initialize_client()
        
        assert result is False