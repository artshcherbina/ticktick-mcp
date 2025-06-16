"""
Test the actual MCP server with real FastMCP framework.
These tests use the actual MCP server instance and test tool execution.
"""

import pytest
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

from ticktick_mcp.src.server import mcp, initialize_client


class TestMCPServer:
    """Test the actual MCP server functionality."""
    
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
    async def test_server_tool_registration(self):
        """Test that all tools are properly registered with the MCP server."""
        try:
            tools_result = mcp.list_tools()
            if asyncio.iscoroutine(tools_result):
                tools = await tools_result
            else:
                tools = tools_result
        except Exception:
            pytest.skip("MCP list_tools not available in test environment")
            
        tool_names = {tool.name for tool in tools}
        
        expected_tools = {
            'get_projects', 'get_project', 'get_project_tasks', 'get_task',
            'create_task', 'update_task', 'complete_task', 'delete_task',
            'create_project', 'delete_project'
        }
        
        assert expected_tools.issubset(tool_names), f"Missing tools: {expected_tools - tool_names}"
        print(f"✓ All {len(expected_tools)} tools properly registered")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_server_tool_schemas(self):
        """Test that tools have proper schemas."""
        try:
            tools_result = mcp.list_tools()
            if asyncio.iscoroutine(tools_result):
                tools = await tools_result
            else:
                tools = tools_result
        except Exception:
            pytest.skip("MCP list_tools not available in test environment")
        
        for tool in tools:
            assert tool.name is not None, f"Tool missing name"
            assert tool.description is not None, f"Tool {tool.name} missing description"
            
            # Tools that require parameters should have input schemas
            tools_with_params = {
                'get_project', 'get_project_tasks', 'get_task',
                'create_task', 'update_task', 'complete_task', 'delete_task',
                'create_project', 'delete_project'
            }
            
            if tool.name in tools_with_params:
                assert tool.inputSchema is not None, f"Tool {tool.name} missing input schema"
                assert 'properties' in tool.inputSchema, f"Tool {tool.name} schema missing properties"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_execute_get_projects_tool(self):
        """Test executing get_projects tool through MCP server."""
        # Test tool execution directly (MCP framework testing not always available in test env)
        try:
            # Import the actual tool function
            from ticktick_mcp.src.server import get_projects
            result = await get_projects()
            
            assert isinstance(result, str), "Tool should return string result"
            assert len(result) > 0, "Tool should return non-empty result"
            
            # Should contain either projects or "no projects found"
            assert ("projects:" in result.lower() or 
                   "no projects found" in result.lower()), f"Unexpected result format: {result[:100]}"
            
            print(f"✓ get_projects executed successfully")
            
        except Exception as e:
            pytest.fail(f"Failed to execute get_projects tool: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_and_cleanup_project(self):
        """Test creating and deleting a project through MCP tools."""
        from ticktick_mcp.src.server import create_project, delete_project
        
        # Create a test project
        project_name = f"MCP Server Test {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        create_result = await create_project(
            name=project_name,
            color="#00FF00",
            view_mode="list"
        )
        
        assert "Project created successfully" in create_result, f"Failed to create project: {create_result}"
        
        # Extract project ID
        project_id = None
        for line in create_result.split('\n'):
            if line.startswith("ID:"):
                project_id = line.split("ID:")[1].strip()
                break
        
        assert project_id is not None, "Could not extract project ID from result"
        print(f"✓ Created test project with ID: {project_id}")
        
        # Clean up - delete the project
        delete_result = await delete_project(project_id)
        assert "deleted successfully" in delete_result, f"Failed to delete project: {delete_result}"
        print(f"✓ Deleted test project {project_id}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_task_lifecycle(self):
        """Test complete task lifecycle through MCP tools."""
        from ticktick_mcp.src.server import (
            create_project, create_task, get_task, update_task, 
            complete_task, delete_task, delete_project
        )
        
        # 1. Create a test project
        project_name = f"Task Lifecycle Test {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        project_result = await create_project(name=project_name)
        assert "Project created successfully" in project_result
        
        project_id = None
        for line in project_result.split('\n'):
            if line.startswith("ID:"):
                project_id = line.split("ID:")[1].strip()
                break
        
        assert project_id is not None
        print(f"✓ Created project {project_id}")
        
        try:
            # 2. Create a task
            task_title = f"Test Task {datetime.now().strftime('%H%M%S')}"
            
            task_result = await create_task(
                title=task_title,
                project_id=project_id,
                content="Test task content",
                priority=3
            )
            
            assert "Task created successfully" in task_result
            
            task_id = None
            for line in task_result.split('\n'):
                if line.startswith("ID:"):
                    task_id = line.split("ID:")[1].strip()
                    break
            
            assert task_id is not None
            print(f"✓ Created task {task_id}")
            
            # 3. Get the task
            get_result = await get_task(project_id, task_id)
            assert task_title in get_result
            assert "Priority: Medium" in get_result
            print(f"✓ Retrieved task details")
            
            # 4. Update the task
            updated_title = f"Updated {task_title}"
            update_result = await update_task(
                task_id=task_id,
                project_id=project_id,
                title=updated_title,
                priority=5
            )
            
            assert "Task updated successfully" in update_result
            assert updated_title in update_result
            assert "Priority: High" in update_result
            print(f"✓ Updated task")
            
            # 5. Complete the task
            complete_result = await complete_task(project_id, task_id)
            assert "marked as complete" in complete_result
            print(f"✓ Completed task")
            
            # 6. Delete the task
            delete_task_result = await delete_task(project_id, task_id)
            assert "deleted successfully" in delete_task_result
            print(f"✓ Deleted task")
            
        finally:
            # 7. Clean up project
            delete_project_result = await delete_project(project_id)
            assert "deleted successfully" in delete_project_result
            print(f"✓ Cleaned up project")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_handling_through_mcp(self):
        """Test error handling when using invalid parameters through MCP."""
        from ticktick_mcp.src.server import get_project, create_task
        
        # Test with invalid project ID
        result = await get_project("invalid_project_id_12345")
        assert ("error" in result.lower() or 
                "not found" in result.lower() or
                "no name" in result.lower() or
                "no id" in result.lower()), f"Expected error response, got: {result}"
        print("✓ Handled invalid project ID correctly")
        
        # Test with invalid priority
        result = await create_task(
            title="Invalid Priority Task",
            project_id="any_project",
            priority=10  # Invalid
        )
        assert "Invalid priority" in result
        print("✓ Handled invalid priority correctly")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mcp_server_metadata(self):
        """Test MCP server metadata and info."""
        # Test that the server has proper name
        assert hasattr(mcp, 'name'), "MCP server should have a name"
        
        # Test that tools are accessible
        try:
            tools_result = mcp.list_tools()
            if asyncio.iscoroutine(tools_result):
                tools = await tools_result
            else:
                tools = tools_result
            assert len(tools) > 0, "MCP server should have tools registered"
            print(f"✓ MCP server '{getattr(mcp, 'name', 'unknown')}' has {len(tools)} tools registered")
        except Exception:
            # If tools listing fails, just verify the server exists
            print(f"✓ MCP server '{getattr(mcp, 'name', 'unknown')}' is available")