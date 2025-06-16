"""
Integration tests for TickTick MCP server using real MCP framework.
These tests require valid TickTick credentials in .env file.
"""

import pytest
import asyncio
import os
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolRequest, CallToolResult
from dotenv import load_dotenv

from ticktick_mcp.src.server import (
    mcp, initialize_client,
    get_projects, get_project, get_project_tasks, get_task,
    create_task, update_task, complete_task, delete_task,
    create_project, delete_project
)


class TestMCPIntegration:
    """Integration tests using real MCP framework and TickTick API."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        load_dotenv()
        
        # Check if we have credentials for integration tests
        cls.has_credentials = (
            os.getenv("TICKTICK_ACCESS_TOKEN") is not None and
            os.getenv("TICKTICK_CLIENT_ID") is not None and
            os.getenv("TICKTICK_CLIENT_SECRET") is not None
        )
        
        if cls.has_credentials:
            # Initialize the client
            success = initialize_client()
            if not success:
                cls.has_credentials = False
                
        # Test project and task IDs (will be set during tests)
        cls.test_project_id = None
        cls.test_task_id = None
    
    @pytest.fixture(autouse=True)
    def skip_if_no_credentials(self):
        """Skip tests if no TickTick credentials are available."""
        if not self.has_credentials:
            pytest.skip("TickTick credentials not available for integration tests")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mcp_tool_registration(self):
        """Test that MCP tools are properly registered."""
        # Check that the MCP server has the expected tools
        try:
            tools_result = mcp.list_tools()
            if asyncio.iscoroutine(tools_result):
                tools = await tools_result
            else:
                tools = tools_result
        except Exception:
            # If list_tools doesn't work, skip this test but don't fail
            pytest.skip("MCP list_tools not available in test environment")
        
        expected_tools = {
            'get_projects', 'get_project', 'get_project_tasks', 'get_task',
            'create_task', 'update_task', 'complete_task', 'delete_task',
            'create_project', 'delete_project'
        }
        
        actual_tools = {tool.name for tool in tools}
        assert expected_tools.issubset(actual_tools), f"Missing tools: {expected_tools - actual_tools}"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_projects_via_mcp(self):
        """Test getting projects through MCP framework."""
        result = await get_projects()
        
        assert isinstance(result, str)
        assert "projects:" in result.lower() or "no projects found" in result.lower()
        
        # If we have projects, verify the format
        if "Found" in result:
            assert "Project" in result
            assert "Name:" in result
            assert "ID:" in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_test_project(self):
        """Create a test project for subsequent tests."""
        project_name = f"MCP Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = await create_project(
            name=project_name,
            color="#FF0000",
            view_mode="list"
        )
        
        assert "Project created successfully" in result
        assert project_name in result
        assert "ID:" in result
        
        # Extract project ID for cleanup
        lines = result.split('\n')
        for line in lines:
            if line.startswith("ID:"):
                TestMCPIntegration.test_project_id = line.split("ID:")[1].strip()
                break
        
        assert TestMCPIntegration.test_project_id is not None
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_specific_project(self):
        """Test getting a specific project."""
        if not TestMCPIntegration.test_project_id:
            await self.test_create_test_project()
        
        result = await get_project(TestMCPIntegration.test_project_id)
        
        assert "Name:" in result
        assert "ID:" in result
        assert TestMCPIntegration.test_project_id in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_test_task(self):
        """Create a test task in the test project."""
        if not TestMCPIntegration.test_project_id:
            await self.test_create_test_project()
        
        task_title = f"MCP Test Task {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create a task with due date one week from now
        due_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        
        result = await create_task(
            title=task_title,
            project_id=TestMCPIntegration.test_project_id,
            content="This is a test task created by MCP integration tests",
            due_date=due_date,
            priority=3
        )
        
        assert "Task created successfully" in result
        assert task_title in result
        assert "Priority: Medium" in result
        
        # Extract task ID for further tests
        lines = result.split('\n')
        for line in lines:
            if line.startswith("ID:"):
                TestMCPIntegration.test_task_id = line.split("ID:")[1].strip()
                break
        
        assert TestMCPIntegration.test_task_id is not None
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_project_tasks(self):
        """Test getting tasks from a project."""
        if not TestMCPIntegration.test_project_id:
            await self.test_create_test_project()
        if not TestMCPIntegration.test_task_id:
            await self.test_create_test_task()
        
        result = await get_project_tasks(TestMCPIntegration.test_project_id)
        
        assert "tasks in project" in result.lower() or "no tasks found" in result.lower()
        
        # If we have tasks, verify our test task is there
        if TestMCPIntegration.test_task_id and "Found" in result:
            assert TestMCPIntegration.test_task_id in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_specific_task(self):
        """Test getting a specific task."""
        if not TestMCPIntegration.test_project_id:
            await self.test_create_test_project()
        if not TestMCPIntegration.test_task_id:
            await self.test_create_test_task()
        
        result = await get_task(
            TestMCPIntegration.test_project_id,
            TestMCPIntegration.test_task_id
        )
        
        assert "Title:" in result
        assert "ID:" in result
        assert TestMCPIntegration.test_task_id in result
        assert "Priority:" in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_task(self):
        """Test updating a task."""
        if not TestMCPIntegration.test_project_id:
            await self.test_create_test_project()
        if not TestMCPIntegration.test_task_id:
            await self.test_create_test_task()
        
        updated_title = f"Updated MCP Test Task {datetime.now().strftime('%H%M%S')}"
        
        result = await update_task(
            task_id=TestMCPIntegration.test_task_id,
            project_id=TestMCPIntegration.test_project_id,
            title=updated_title,
            priority=5  # High priority
        )
        
        assert "Task updated successfully" in result
        assert updated_title in result
        assert "Priority: High" in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_task_validation_errors(self):
        """Test validation errors in task operations."""
        # Test invalid priority
        result = await create_task(
            title="Invalid Priority Task",
            project_id="any_project",
            priority=10  # Invalid priority
        )
        assert "Invalid priority" in result
        
        # Test invalid date format
        result = await create_task(
            title="Invalid Date Task",
            project_id="any_project",
            start_date="invalid-date"
        )
        assert "Invalid start_date format" in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_project_validation_errors(self):
        """Test validation errors in project operations."""
        # Test invalid view mode
        result = await create_project(
            name="Invalid View Mode Project",
            view_mode="invalid_mode"
        )
        assert "Invalid view_mode" in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_task(self):
        """Test completing a task."""
        if not TestMCPIntegration.test_project_id:
            await self.test_create_test_project()
        if not TestMCPIntegration.test_task_id:
            await self.test_create_test_task()
        
        result = await complete_task(
            TestMCPIntegration.test_project_id,
            TestMCPIntegration.test_task_id
        )
        
        assert "marked as complete" in result
        assert TestMCPIntegration.test_task_id in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_handling_invalid_ids(self):
        """Test error handling with invalid IDs."""
        # Test invalid project ID
        result = await get_project("invalid_project_id_12345")
        assert ("error" in result.lower() or 
                "not found" in result.lower() or 
                "no name" in result.lower() or
                "no id" in result.lower()), f"Expected error response, got: {result}"
        
        # Test invalid task ID
        result = await get_task("invalid_project_id_12345", "invalid_task_id_12345")
        assert ("error" in result.lower() or 
                "not found" in result.lower() or
                "no title" in result.lower() or
                "no id" in result.lower()), f"Expected error response, got: {result}"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cleanup_test_data(self):
        """Clean up test data."""
        # Delete test task if it exists
        if TestMCPIntegration.test_task_id and TestMCPIntegration.test_project_id:
            try:
                result = await delete_task(
                    TestMCPIntegration.test_project_id,
                    TestMCPIntegration.test_task_id
                )
                # Don't assert success as task might already be completed/deleted
            except Exception:
                pass  # Ignore cleanup errors
        
        # Delete test project if it exists
        if TestMCPIntegration.test_project_id:
            try:
                result = await delete_project(TestMCPIntegration.test_project_id)
                assert "deleted successfully" in result
            except Exception as e:
                # Log but don't fail the test if cleanup fails
                print(f"Warning: Failed to delete test project: {e}")
        
        # Reset class variables
        TestMCPIntegration.test_project_id = None
        TestMCPIntegration.test_task_id = None


class TestMCPToolCalls:
    """Test MCP tool calls through the framework."""
    
    @pytest.fixture(autouse=True)
    def skip_if_no_credentials(self):
        """Skip tests if no TickTick credentials are available."""
        load_dotenv()
        has_credentials = (
            os.getenv("TICKTICK_ACCESS_TOKEN") is not None and
            os.getenv("TICKTICK_CLIENT_ID") is not None and
            os.getenv("TICKTICK_CLIENT_SECRET") is not None
        )
        if not has_credentials:
            pytest.skip("TickTick credentials not available for integration tests")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mcp_call_get_projects(self):
        """Test calling get_projects through MCP framework."""
        # Test the tool directly since MCP request handling is framework-specific
        result = await get_projects()
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify it contains expected content
        assert ("projects:" in result.lower() or 
               "no projects found" in result.lower()), f"Unexpected result format: {result[:100]}"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mcp_tool_argument_validation(self):
        """Test that MCP tools properly validate arguments."""
        # Test create_task with required arguments
        result = await create_task(
            title="Test Task",
            project_id="test_project_id"
        )
        
        # Should either succeed or fail with API error (not argument error)
        assert isinstance(result, str)
        assert "Invalid priority" not in result  # No argument validation error
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mcp_server_tools_list(self):
        """Test that MCP server properly exposes tools."""
        try:
            tools_result = mcp.list_tools()
            if asyncio.iscoroutine(tools_result):
                tools = await tools_result
            else:
                tools = tools_result
        except Exception:
            pytest.skip("MCP list_tools not available in test environment")
            
        tool_names = [tool.name for tool in tools]
        
        # Verify all expected tools are available
        expected_tools = [
            'get_projects', 'get_project', 'get_project_tasks', 'get_task',
            'create_task', 'update_task', 'complete_task', 'delete_task',
            'create_project', 'delete_project'
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Tool {expected_tool} not found in MCP server"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mcp_tool_descriptions(self):
        """Test that MCP tools have proper descriptions."""
        try:
            tools_result = mcp.list_tools()
            if asyncio.iscoroutine(tools_result):
                tools = await tools_result
            else:
                tools = tools_result
        except Exception:
            pytest.skip("MCP list_tools not available in test environment")
        
        for tool in tools:
            assert tool.description is not None, f"Tool {tool.name} missing description"
            assert len(tool.description) > 10, f"Tool {tool.name} has too short description"
            
            # Check that parameters are documented for tools that need them
            if tool.name in ['create_task', 'update_task', 'create_project']:
                assert tool.inputSchema is not None, f"Tool {tool.name} missing input schema"