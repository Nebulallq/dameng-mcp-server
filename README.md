# DaMeng MCP Server

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-orange.svg)](https://modelcontextprotocol.io/)

A Model Context Protocol (MCP) server for DaMeng (达梦) Database, enabling LLMs to interact with DaMeng databases through standardized tools and resources.

## Features

- **SQL Query Execution**: Execute any SQL query on DaMeng database
- **Table Resources**: Access database tables as MCP resources
- **Schema Discovery**: Automatically discover and list available tables
- **Connection Pooling**: Efficient database connection management
- **Error Handling**: Comprehensive error handling and logging
- **Type Hints**: Full type annotations for better IDE support

## Installation

### Prerequisites

- Python 3.9 or higher
- DaMeng Database server running
- dmPython driver installed

### Install from source

```bash
git clone https://github.com/yourusername/dameng-mcp-server.git
cd dameng-mcp-server
pip install -e .
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Install dmPython Driver

```bash
pip install dmPython
```

Or download from [DaMeng Official Website](https://www.dameng.com/)

## Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DAMENG_HOST=localhost
DAMENG_PORT=5236
DAMENG_USER=SYSDBA
DAMENG_PASSWORD=your_password
DAMENG_DATABASE=your_schema

# Optional: Logging
LOG_LEVEL=INFO
```

## Usage

### Running the Server

```bash
python -m dameng_mcp_server
```

### Using with Claude Desktop

Add to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "dameng": {
      "command": "python",
      "args": ["-m", "dameng_mcp_server"],
      "env": {
        "DAMENG_HOST": "localhost",
        "DAMENG_PORT": "5236",
        "DAMENG_USER": "SYSDBA",
        "DAMENG_PASSWORD": "your_password"
      }
    }
  }
}
```

## Usage

### Using the Python Client

An interactive Python client is provided with AI capabilities:

```bash
cd examples
python mcp_client.py
```

The client supports the following commands:
- `/sql <query>` - Execute SQL directly
- `/tables [pattern]` - List tables
- `/describe <table>` - Describe table structure
- `/schemas [pattern]` - List schemas
- `/quit` - Exit

### Using with Claude Desktop

Add to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "dameng": {
      "command": "python",
      "args": ["-m", "dameng_mcp_server"],
      "env": {
        "DAMENG_HOST": "localhost",
        "DAMENG_PORT": "5236",
        "DAMENG_USER": "SYSDBA",
        "DAMENG_PASSWORD": "your_password"
      }
    }
  }
}
```

### Basic Python Usage

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "dameng_mcp_server"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize session
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")

            # Execute a query
            result = await session.call_tool(
                "execute_sql",
                {"query": "SELECT * FROM your_table LIMIT 10"}
            )
            print(result.content[0].text)

asyncio.run(main())
```

## Available Tools

### execute_sql

Execute SQL queries on the DaMeng database.

**Parameters:**
- `query` (string, required): The SQL query to execute

**Example:**
```python
result = await session.call_tool("execute_sql", {
    "query": "SELECT COUNT(*) FROM users"
})
```

### list_tables

List all tables in the database.

**Parameters:**
- `pattern` (string, optional): Filter table names by pattern (e.g., 'SYS%')

**Example:**
```python
result = await session.call_tool("list_tables", {
    "pattern": "SYS%"
})
```

### describe_table

Get detailed information about a table's structure.

**Parameters:**
- `table_name` (string, required): The name of the table

**Example:**
```python
result = await session.call_tool("describe_table", {
    "table_name": "SYSUSER"
})
```

### get_schema_info

Get information about database schemas.

**Parameters:**
- `schema_pattern` (string, optional): Filter schemas by pattern

**Example:**
```python
result = await session.call_tool("get_schema_info", {
    "schema_pattern": "SYS%"
})
```

## Available Resources

Database tables are exposed as resources with the URI pattern:
```
dameng://{table_name}/data
```

**Example:**
```python
# Read a table as a resource
resource = await session.read_resource("dameng://users/data")
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
isort src/
```

### Type Checking

```bash
mypy src/
```

## Project Structure

```
dameng-mcp-server/
├── src/
│   └── dameng_mcp_server/
│       ├── __init__.py
│       ├── server.py          # Main MCP server implementation
│       ├── config.py          # Configuration management
│       ├── database.py        # Database connection handling
│       └── tools.py           # MCP tool definitions
├── tests/
│   ├── __init__.py
│   ├── test_server.py
│   └── test_database.py
├── examples/
│   ├── basic_client.py        # Basic usage example
│   └── advanced_client.py     # Advanced usage example
├── docs/
│   ├── installation.md
│   └── api.md
├── .env.example               # Example environment variables
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml             # Project configuration
└── requirements.txt           # Dependencies
```

## API Reference

### Server Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `DAMENG_HOST` | Database host | `localhost` |
| `DAMENG_PORT` | Database port | `5236` |
| `DAMENG_USER` | Database user | `SYSDBA` |
| `DAMENG_PASSWORD` | Database password | (required) |
| `DAMENG_DATABASE` | Database/schema name | `""` |

## Debugging

### Quick Debug

Run the built-in debug script:

```bash
python debug.py
```

This will check:
- Python version
- Dependencies
- Environment configuration
- Database connection
- Project structure

For detailed debugging guide, see [DEBUGGING.md](docs/debugging.md).

## Troubleshooting

### Connection Issues

1. Verify DaMeng database is running:
```bash
# Check if port 5236 is accessible
telnet localhost 5236
```

2. Check credentials in `.env` file

3. Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

### Common Errors

- **Missing dmPython**: Install with `pip install dmPython`
- **Connection refused**: Check DAMENG_HOST and DAMENG_PORT
- **Authentication failed**: Verify DAMENG_USER and DAMENG_PASSWORD

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol specification
- [DaMeng Database](https://www.dameng.com/) - The database system
- [dmPython](https://github.com/dameng/DmPython) - The Python driver

## Support

- Issues: [GitHub Issues](https://github.com/yourusername/dameng-mcp-server/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/dameng-mcp-server/discussions)

## Roadmap

- [ ] Add connection pooling support
- [ ] Implement transaction management tools
- [ ] Add query result caching
- [ ] Support for prepared statements
- [ ] Add streaming result support
- [ ] Implement database backup/restore tools
