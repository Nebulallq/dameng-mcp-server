"""
Main MCP server implementation for DaMeng Database.
"""

import asyncio
import logging
import sys
from typing import List

from mcp.server import Server
from mcp.types import Resource, TextContent, Tool
from pydantic import AnyUrl

from dameng_mcp_server.config import ServerConfig
from dameng_mcp_server.database import DatabaseManager
from dameng_mcp_server.tools import ToolDefinitions, ToolExecutor

# Initialize server
app = Server("dameng_mcp_server")

# Global configuration and database manager
_config: ServerConfig | None = None
_db_manager: DatabaseManager | None = None
_tool_executor: ToolExecutor | None = None
logger = logging.getLogger("dameng_mcp_server.server")


def get_config() -> ServerConfig:
    """Get or create server configuration."""
    global _config
    if _config is None:
        _config = ServerConfig.from_env()
        _config.setup_logging()
    return _config


def get_db_manager() -> DatabaseManager:
    """Get or create database manager."""
    global _db_manager
    if _db_manager is None:
        config = get_config()
        _db_manager = DatabaseManager(config.db_config)
    return _db_manager


def get_tool_executor() -> ToolExecutor:
    """Get or create tool executor."""
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutor(get_db_manager())
    return _tool_executor


@app.list_resources()
async def list_resources() -> List[Resource]:
    """
    List Dameng tables as MCP resources.

    Returns:
        List[Resource]: List of available table resources
    """
    try:
        db_manager = get_db_manager()
        tables = db_manager.list_tables()
        logger.info(f"Found {len(tables)} tables for resources")

        resources = []
        for table in tables:
            resources.append(
                Resource(
                    uri=f"dameng://{table}/data",
                    name=f"Table: {table}",
                    mimeType="text/plain",
                    description=f"Data in table: {table}",
                )
            )
        return resources
    except Exception as e:
        logger.error(f"Failed to list resources: {str(e)}")
        return []


@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """
    Read table contents as an MCP resource.

    Args:
        uri: Resource URI in format dameng://table_name/data

    Returns:
        str: Table data as CSV

    Raises:
        ValueError: If URI format is invalid
        RuntimeError: If reading fails
    """
    uri_str = str(uri)
    logger.info(f"Reading resource: {uri_str}")

    if not uri_str.startswith("dameng://"):
        raise ValueError(f"Invalid URI scheme: {uri_str}. Expected 'dameng://'")

    # Extract table name from URI
    parts = uri_str[len("dameng://") :]
    if "/data" not in parts:
        raise ValueError(f"Invalid URI format: {uri_str}. Expected 'dameng://table_name/data'")

    table = parts.split("/")[0]

    try:
        db_manager = get_db_manager()
        columns, rows, _ = db_manager.execute_query(f"SELECT * FROM {table} LIMIT 100")

        if columns is None:
            return f"Table '{table}' does not exist or cannot be queried"

        if rows:
            return db_manager.format_query_result(columns, rows)

        return f"Table '{table}' is empty. Columns: {', '.join(columns)}"

    except Exception as e:
        logger.error(f"Error reading resource {uri}: {str(e)}")
        raise RuntimeError(f"Error reading resource: {str(e)}") from e


@app.list_tools()
async def list_tools() -> List[Tool]:
    """
    List available Dameng database tools.

    Returns:
        List[Tool]: List of available tools
    """
    logger.debug("Listing tools...")
    return ToolDefinitions.get_all_tools()


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """
    Execute a tool call.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List[TextContent]: Tool execution result

    Raises:
        ValueError: If tool execution fails
    """
    try:
        executor = get_tool_executor()
        result = await executor.execute_tool(name, arguments)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        logger.error(f"Error executing tool '{name}': {e}")
        error_msg = f"Error executing tool '{name}': {str(e)}"
        return [TextContent(type="text", text=error_msg)]


async def main():
    """Main entry point to run the MCP server."""
    from mcp.server.stdio import stdio_server

    # Get and display configuration
    config = get_config()
    db_config = config.db_config

    # Add debug output
    print("Starting DaMeng MCP server...", file=sys.stderr)
    print(f"Server: {db_config.server}", file=sys.stderr)
    print(f"Port: {db_config.port}", file=sys.stderr)
    print(f"User: {db_config.user}", file=sys.stderr)
    print(f"Schema: {db_config.schema or 'default'}", file=sys.stderr)

    logger.info("Starting DaMeng MCP server...")
    logger.info(
        f"Database config: {db_config.server}:{db_config.port}/{db_config.schema} as {db_config.user}"
    )

    async with stdio_server() as (read_stream, write_stream):
        try:
            await app.run(read_stream, write_stream, app.create_initialization_options())
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
