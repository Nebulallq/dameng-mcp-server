"""
Basic MCP client example for DaMeng MCP Server.

This example demonstrates how to:
1. Connect to the MCP server
2. List available tools
3. Execute a simple SQL query
"""

import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Optional: For database configuration
from dotenv import load_dotenv

load_dotenv()


async def main():
    """Run the basic client example."""

    # Configure server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "dameng_mcp_server"],
        env={
            "DAMENG_HOST": os.getenv("DAMENG_HOST", "localhost"),
            "DAMENG_PORT": os.getenv("DAMENG_PORT", "5236"),
            "DAMENG_USER": os.getenv("DAMENG_USER", "SYSDBA"),
            "DAMENG_PASSWORD": os.getenv("DAMENG_PASSWORD", ""),
        },
    )

    print("🔌 Connecting to DaMeng MCP Server...")

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the session
            await session.initialize()
            print("✅ Connected!\n")

            # List available tools
            tools_response = await session.list_tools()
            print("📦 Available Tools:")
            for tool in tools_response.tools:
                print(f"  - {tool.name}: {tool.description}")
            print()

            # List available resources (tables)
            resources_response = await session.list_resources()
            print(f"📊 Available Resources (Tables): {len(resources_response.resources)}")
            for resource in resources_response.resources[:5]:  # Show first 5
                print(f"  - {resource.name}: {resource.uri}")
            if len(resources_response.resources) > 5:
                print(f"  ... and {len(resources_response.resources) - 5} more")
            print()

            # Example 1: List all tables
            print("🔍 Example 1: Listing all tables")
            result = await session.call_tool("list_tables", {})
            print(f"Result:\n{result.content[0].text}\n")

            # Example 2: Execute a simple query (modify table name as needed)
            print("🔍 Example 2: Executing a custom query")
            query = "SELECT COUNT(*) as table_count FROM ALL_TABLES"
            result = await session.call_tool("execute_sql", {"query": query})
            print(f"Query: {query}")
            print(f"Result:\n{result.content[0].text}\n")

            # Example 3: Describe a table (modify table name as needed)
            print("🔍 Example 3: Describing a table")
            # Get first table name from resources
            if resources_response.resources:
                first_table = resources_response.resources[0].name.replace("Table: ", "")
                result = await session.call_tool("describe_table", {"table_name": first_table})
                print(f"Table: {first_table}")
                print(f"Result:\n{result.content[0].text}\n")

            print("✅ Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
