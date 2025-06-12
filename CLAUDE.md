# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

- **Install dependencies**: `uv pip install -e .`
- **Install dev dependencies**: `uv pip install -e ".[dev]"`
- **Run all tests**: `uv run pytest`
- **Run unit tests only**: `uv run pytest -m "not integration"`
- **Run integration tests**: `uv run pytest -m integration` (requires TickTick credentials)
- **Run specific test file**: `uv run pytest tests/test_mcp_tools.py`
- **Run tests with verbose output**: `uv run pytest -v`
- **Run tests with coverage**: `uv run pytest --cov=ticktick_mcp`
- **Run authentication**: `uv run -m ticktick_mcp.cli auth`
- **Test server configuration**: `uv run test_server.py`
- **Run MCP server**: `uv run -m ticktick_mcp.cli run`
- **Run server with debug logging**: `uv run -m ticktick_mcp.cli run --debug`

## Code Architecture

This is a Model Context Protocol (MCP) server that provides TickTick integration for Claude and other MCP clients.

### Core Components

- **ticktick_mcp/src/server.py**: Main MCP server implementation using FastMCP framework. Contains all MCP tool definitions (@mcp.tool() decorated functions) for project and task management.
- **ticktick_mcp/src/ticktick_client.py**: TickTickClient class that handles OAuth2 authentication and API requests to TickTick's REST API. Includes automatic token refresh.
- **ticktick_mcp/cli.py**: Command-line interface that handles server startup and authentication flows.
- **ticktick_mcp/authenticate.py**: OAuth2 authentication flow implementation with local server for callback handling.

### Authentication Flow

The project uses OAuth2 with automatic token refresh:
1. Client credentials (ID/Secret) stored in .env
2. OAuth flow opens browser for user authorization  
3. Local server captures authorization code
4. Tokens exchanged and stored in .env
5. Automatic token refresh on API calls

### MCP Tools Available

The server exposes these tools to MCP clients:
- Project management: get_projects, get_project, create_project, delete_project
- Task management: get_project_tasks, get_task, create_task, update_task, complete_task, delete_task

### Configuration

- Environment variables stored in .env file
- Supports both TickTick and Dida365 (Chinese version) via base URL configuration
- Uses uv for Python package management
- FastMCP server runs on stdio transport for MCP communication