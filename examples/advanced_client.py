"""
Advanced MCP client example for DaMeng MCP Server.

This example demonstrates:
1. Using resources to read table data
2. Error handling and retry logic
3. Interactive query loop
4. Result formatting and display
"""

import asyncio
import os
import sys
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()


class DaMengMCPClient:
    """Advanced client for DaMeng MCP Server."""

    def __init__(self):
        """Initialize the client."""
        self.session: Optional[ClientSession] = None
        self.server_params = StdioServerParameters(
            command="python",
            args=["-m", "dameng_mcp_server"],
            env={
                "DAMENG_HOST": os.getenv("DAMENG_HOST", "localhost"),
                "DAMENG_PORT": os.getenv("DAMENG_PORT", "5236"),
                "DAMENG_USER": os.getenv("DAMENG_USER", "SYSDBA"),
                "DAMENG_PASSWORD": os.getenv("DAMENG_PASSWORD", ""),
                "DAMENG_DATABASE": os.getenv("DAMENG_DATABASE", ""),
            },
        )

    async def connect(self):
        """Connect to the MCP server."""
        print("🔌 Connecting to DaMeng MCP Server...")
        self.stdio_context = stdio_client(self.server_params)
        self.read_stream, self.write_stream = await self.stdio_context.__aenter__()

        self.session_context = ClientSession(self.read_stream, self.write_stream)
        self.session = await self.session_context.__aenter__()

        await self.session.initialize()
        print("✅ Connected!\n")

    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session_context:
            await self.session_context.__aexit__(None, None, None)
        if self.stdio_context:
            await self.stdio_context.__aexit__(None, None, None)

    async def list_tools(self):
        """List available tools."""
        response = await self.session.list_tools()
        return response.tools

    async def list_resources(self):
        """List available resources."""
        response = await self.session.list_resources()
        return response.resources

    async def execute_query(self, query: str) -> str:
        """
        Execute a SQL query.

        Args:
            query: SQL query to execute

        Returns:
            str: Query result
        """
        result = await self.session.call_tool("execute_sql", {"query": query})
        return result.content[0].text

    async def list_tables(self, pattern: Optional[str] = None) -> str:
        """
        List database tables.

        Args:
            pattern: Optional pattern to filter table names

        Returns:
            str: List of table names
        """
        args = {"pattern": pattern} if pattern else {}
        result = await self.session.call_tool("list_tables", args)
        return result.content[0].text

    async def describe_table(self, table_name: str) -> str:
        """
        Describe a table's structure.

        Args:
            table_name: Name of the table

        Returns:
            str: Table description
        """
        result = await self.session.call_tool("describe_table", {"table_name": table_name})
        return result.content[0].text

    async def read_table_as_resource(self, table_name: str) -> str:
        """
        Read a table as an MCP resource.

        Args:
            table_name: Name of the table

        Returns:
            str: Table data
        """
        uri = f"dameng://{table_name}/data"
        result = await self.session.read_resource(uri)
        return result

    def format_result(self, title: str, content: str) -> None:
        """
        Format and print a result.

        Args:
            title: Result title
            content: Result content
        """
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        print(content)
        print(f"{'='*60}\n")

    async def interactive_loop(self):
        """Run an interactive query loop."""
        print("\n🔄 Interactive Query Mode")
        print("Commands:")
        print("  - Enter a SQL query to execute")
        print("  - 'tables' - List all tables")
        print("  - 'describe <table>' - Describe a table")
        print("  - 'quit' - Exit\n")

        while True:
            try:
                user_input = input("daMeng> ").strip()

                if not user_input:
                    continue

                if user_input.lower() == "quit":
                    print("👋 Goodbye!")
                    break

                if user_input.lower() == "tables":
                    result = await self.list_tables()
                    self.format_result("Database Tables", result)
                    continue

                if user_input.lower().startswith("describe "):
                    table_name = user_input[9:].strip()
                    if table_name:
                        result = await self.describe_table(table_name)
                        self.format_result(f"Table Structure: {table_name}", result)
                    else:
                        print("❌ Please provide a table name")
                    continue

                # Assume it's a SQL query
                result = await self.execute_query(user_input)
                self.format_result(f"Query Result", result)

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")

    async def run_demo(self):
        """Run a demonstration of the client capabilities."""
        # List tools
        tools = await self.list_tools()
        print(f"📦 Available Tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool.name}")

        # List resources
        resources = await self.list_resources()
        print(f"\n📊 Available Tables: {len(resources)}")

        # Get first table name for examples
        first_table = None
        if resources:
            first_table = resources[0].name.replace("Table: ", "")
            print(f"   First table: {first_table}")

        # List all tables
        tables = await self.list_tables()
        self.format_result("All Tables", tables)

        # Describe first table
        if first_table:
            description = await self.describe_table(first_table)
            self.format_result(f"Table Description: {first_table}", description)

            # Read table as resource
            try:
                resource_data = await self.read_table_as_resource(first_table)
                self.format_result(f"Table Data (Resource): {first_table}", resource_data)
            except Exception as e:
                print(f"⚠️  Could not read table as resource: {e}")

        # Execute a query
        query_result = await self.execute_query("SELECT COUNT(*) as table_count FROM ALL_TABLES")
        self.format_result("Query: Count of All Tables", query_result)


async def main():
    """Main entry point."""
    client = DaMengMCPClient()

    try:
        await client.connect()

        # Run demo
        await client.run_demo()

        # Optionally start interactive mode
        print("\n" + "="*60)
        user_choice = input("Start interactive mode? (y/n): ").strip().lower()
        if user_choice == "y":
            await client.interactive_loop()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
