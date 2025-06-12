"""
Test for specific task retrieval from real TickTick data.
This test gets information about the "1ч Логотип" task from the "Сайт" project.
"""

import pytest
import os
from dotenv import load_dotenv

from ticktick_mcp.src.server import (
    initialize_client, get_projects, get_project_tasks, get_task
)


class TestSpecificTaskRetrieval:
    """Test retrieval of specific task from real TickTick data."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        load_dotenv()
        cls.has_credentials = (
            os.getenv("TICKTICK_ACCESS_TOKEN") is not None and
            os.getenv("TICKTICK_CLIENT_ID") is not None and
            os.getenv("TICKTICK_CLIENT_SECRET") is not None
        )
        
        if cls.has_credentials:
            success = initialize_client()
            if not success:
                cls.has_credentials = False
    
    @pytest.fixture(autouse=True)
    def skip_if_no_credentials(self):
        """Skip tests if no TickTick credentials are available."""
        if not self.has_credentials:
            pytest.skip("TickTick credentials not available - run 'uv run -m ticktick_mcp.cli auth' first")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_site_project(self):
        """Find the 'Сайт' project and get its ID."""
        result = await get_projects()
        
        assert isinstance(result, str)
        assert "projects:" in result.lower() or "found" in result.lower()
        
        # Look for the Сайт project
        assert "Сайт" in result, f"Сайт project not found in projects list. Available projects: {result}"
        
        # Extract project ID for Сайт project
        lines = result.split('\n')
        site_project_id = None
        
        for i, line in enumerate(lines):
            if "Сайт" in line and "Name:" in line:
                # Look for ID in the next few lines
                for j in range(i, min(i + 5, len(lines))):
                    if lines[j].startswith("ID:"):
                        site_project_id = lines[j].split("ID:")[1].strip()
                        break
                break
        
        assert site_project_id is not None, f"Could not find ID for Сайт project in: {result}"
        print(f"✓ Found Сайт project with ID: {site_project_id}")
        
        return site_project_id
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_site_project_tasks(self):
        """Get all tasks from the Сайт project."""
        # First get the project ID
        site_project_id = await self.test_find_site_project()
        
        # Get tasks from the project
        result = await get_project_tasks(site_project_id)
        
        assert isinstance(result, str)
        print(f"Tasks in Сайт project:\n{result}")
        
        return site_project_id, result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_logo_task(self):
        """Find the '1ч Логотип' task in the Сайт project."""
        site_project_id, tasks_result = await self.test_get_site_project_tasks()
        
        # Look for the "1ч Логотип" task
        if "no tasks found" in tasks_result.lower():
            pytest.skip("No tasks found in Сайт project")
        
        # Check if the logo task exists
        if "1ч Логотип" not in tasks_result:
            print(f"Available tasks in Сайт project: {tasks_result}")
            pytest.skip("1ч Логотип task not found in Сайт project")
        
        # Extract task ID for the logo task
        lines = tasks_result.split('\n')
        logo_task_id = None
        
        for i, line in enumerate(lines):
            if "1ч Логотип" in line and "Title:" in line:
                # Look backwards for ID in the previous few lines (ID comes before Title)
                for j in range(max(0, i-5), i):
                    if lines[j].startswith("ID:"):
                        logo_task_id = lines[j].split("ID:")[1].strip()
                        break
                # If not found backwards, look forwards
                if logo_task_id is None:
                    for j in range(i, min(i + 5, len(lines))):
                        if lines[j].startswith("ID:"):
                            logo_task_id = lines[j].split("ID:")[1].strip()
                            break
                break
        
        assert logo_task_id is not None, f"Could not find ID for 1ч Логотип task in: {tasks_result}"
        print(f"✓ Found 1ч Логотип task with ID: {logo_task_id}")
        
        return site_project_id, logo_task_id
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_logo_task_details(self):
        """Get detailed information about the '1ч Логотип' task."""
        site_project_id, logo_task_id = await self.test_find_logo_task()
        
        # Get detailed task information
        result = await get_task(site_project_id, logo_task_id)
        
        assert isinstance(result, str)
        assert "Title:" in result
        assert "1ч Логотип" in result
        assert "ID:" in result
        assert logo_task_id in result
        
        print(f"✓ Logo task details:\n{result}")
        
        # Verify expected task information
        assert "Project ID:" in result
        assert site_project_id in result
        
        # Check if task has additional information
        if "Priority:" in result:
            print("✓ Task has priority information")
        if "Status:" in result:
            print("✓ Task has status information")
        if "Content:" in result:
            print("✓ Task has content/description")
        if "Due Date:" in result:
            print("✓ Task has due date")
        if "Start Date:" in result:
            print("✓ Task has start date")
        
        return result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_logo_task_comprehensive_info(self):
        """Get comprehensive information about the logo task and validate structure."""
        task_details = await self.test_get_logo_task_details()
        
        # Parse the task details
        task_info = {}
        lines = task_details.split('\n')
        
        for line in lines:
            if ':' in line and not line.startswith(' '):
                key, value = line.split(':', 1)
                task_info[key.strip()] = value.strip()
        
        # Validate required fields
        assert 'ID' in task_info, "Task missing ID"
        assert 'Title' in task_info, "Task missing Title"
        assert 'Project ID' in task_info, "Task missing Project ID"
        assert 'Status' in task_info, "Task missing Status"
        
        # Print comprehensive task information
        print("\n" + "="*50)
        print("COMPREHENSIVE TASK INFORMATION")
        print("="*50)
        
        for key, value in task_info.items():
            print(f"{key:15}: {value}")
        
        print("="*50)
        
        # Verify task title
        assert task_info['Title'] == '1ч Логотип', f"Expected title '1ч Логотип', got '{task_info['Title']}'"
        
        # Return structured task information
        return task_info
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_logo_task_project_context(self):
        """Test the logo task in the context of its project."""
        task_info = await self.test_logo_task_comprehensive_info()
        
        # Get project information
        project_id = task_info['Project ID']
        site_project_id, tasks_result = await self.test_get_site_project_tasks()
        
        assert project_id == site_project_id, f"Task project ID {project_id} doesn't match Сайт project ID {site_project_id}"
        
        # Verify the task appears in project task list
        assert task_info['ID'] in tasks_result, "Logo task ID not found in project tasks list"
        assert task_info['Title'] in tasks_result, "Logo task title not found in project tasks list"
        
        print(f"✓ Logo task properly linked to Сайт project")
        print(f"✓ Task ID {task_info['ID']} confirmed in project {project_id}")
        
        return True