"""
MCP tool definitions for DaMeng MCP Server.
"""

import logging
from typing import Any, Dict, List

from mcp.types import Tool

logger = logging.getLogger("dameng_mcp_server.tools")


class ToolDefinitions:
    """Definitions of available MCP tools."""

    @staticmethod
    def get_all_tools() -> List[Tool]:
        """
        Get all available tool definitions.

        Returns:
            List[Tool]: List of available tools
        """
        return [
            ToolDefinitions.execute_sql(),
            ToolDefinitions.list_tables(),
            ToolDefinitions.describe_table(),
            ToolDefinitions.get_schema_info(),
        ]

    @staticmethod
    def execute_sql() -> Tool:
        """
        Execute SQL query tool definition.

        Returns:
            Tool: The execute_sql tool definition
        """
        return Tool(
            name="execute_sql",
            description="Execute an SQL query on the DaMeng database. "
            "Supports SELECT, INSERT, UPDATE, DELETE, and other SQL statements. "
            "For SELECT queries, returns the result set as CSV formatted text. "
            "For other queries, returns the number of rows affected.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute. "
                        "Can be any valid SQL statement for DaMeng database.",
                    }
                },
                "required": ["query"],
            },
        )

    @staticmethod
    def list_tables() -> Tool:
        """
        List tables tool definition.

        Returns:
            Tool: The list_tables tool definition
        """
        return Tool(
            name="list_tables",
            description="List all tables available in the DaMeng database. "
            "Returns a list of table names that can be queried.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Optional pattern to filter table names. "
                        "Supports SQL LIKE pattern matching (e.g., 'SYS%' for system tables).",
                    }
                },
            },
        )

    @staticmethod
    def describe_table() -> Tool:
        """
        Describe table tool definition.

        Returns:
            Tool: The describe_table tool definition
        """
        return Tool(
            name="describe_table",
            description="Get detailed information about a specific table's structure, "
            "including column names, data types, and nullability.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "The name of the table to describe.",
                    }
                },
                "required": ["table_name"],
            },
        )

    @staticmethod
    def get_schema_info() -> Tool:
        """
        Get schema info tool definition.

        Returns:
            Tool: The get_schema_info tool definition
        """
        return Tool(
            name="get_schema_info",
            description="Get information about database schemas, users, and their objects. "
            "Returns schema names, owners, and object counts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "schema_pattern": {
                        "type": "string",
                        "description": "Optional pattern to filter schemas (e.g., 'SYS%' for system schemas).",
                    }
                },
            },
        )


class ToolExecutor:
    """Executor for MCP tool calls."""

    def __init__(self, db_manager):
        """
        Initialize the tool executor.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.logger = logging.getLogger("dameng_mcp_server.tools.executor")

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool by name with arguments.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            str: Tool execution result

        Raises:
            ValueError: If tool name is unknown or arguments are invalid
        """
        self.logger.info(f"Executing tool: {name} with arguments: {arguments}")

        if name == "execute_sql":
            return await self._execute_sql(arguments)
        elif name == "list_tables":
            return await self._list_tables(arguments)
        elif name == "describe_table":
            return await self._describe_table(arguments)
        elif name == "get_schema_info":
            return await self._get_schema_info(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _execute_sql(self, arguments: Dict[str, Any]) -> str:
        """
        Execute SQL query tool.

        Args:
            arguments: Tool arguments

        Returns:
            str: Query results or status message
        """
        query = arguments.get("query")
        if not query:
            raise ValueError("Query is required for execute_sql tool")

        columns, rows, affected = self.db_manager.execute_query(query)

        if columns is not None:
            # SELECT query - return formatted results
            if rows:
                return self.db_manager.format_query_result(columns, rows)
            return f"No results found. Columns: {', '.join(columns)}"

        # Non-SELECT query
        return f"Query executed successfully. Rows affected: {affected}"

    async def _list_tables(self, arguments: Dict[str, Any]) -> str:
        """
        List tables tool.

        Args:
            arguments: Tool arguments

        Returns:
            str: List of table names
        """
        pattern = arguments.get("pattern")
        tables = self.db_manager.list_tables()

        if pattern:
            # Filter by pattern
            import re

            regex_pattern = pattern.replace("%", ".*").replace("_", ".")
            matched = [t for t in tables if re.match(regex_pattern, t, re.IGNORECASE)]
            tables = matched

        return "\n".join(tables) if tables else "No tables found"

    async def _describe_table(self, arguments: Dict[str, Any]) -> str:
        """
        Describe table tool.

        Args:
            arguments: Tool arguments

        Returns:
            str: Table structure information
        """
        table_name = arguments.get("table_name")
        if not table_name:
            raise ValueError("table_name is required for describe_table tool")

        columns = self.db_manager.get_table_info(table_name)

        if not columns:
            return f"Table '{table_name}' not found or has no columns"

        # Format as table
        result = [f"Table: {table_name}", ""]
        result.append("Column Name | Data Type | Nullable")
        result.append("-" * 50)
        for col_name, data_type, nullable in columns:
            result.append(f"{col_name} | {data_type} | {nullable}")

        return "\n".join(result)

    async def _get_schema_info(self, arguments: Dict[str, Any]) -> str:
        """
        Get schema info tool.

        Args:
            arguments: Tool arguments

        Returns:
            str: Schema information
        """
        pattern = arguments.get("schema_pattern")
        schemas = self.db_manager.get_schema_info(pattern)

        if not schemas:
            return "No schemas found"

        # Format as table
        result = ["Schema | Owner | Object Count", "-" * 50]
        for schema, owner, count in schemas:
            result.append(f"{schema} | {owner} | {count}")

        return "\n".join(result)
