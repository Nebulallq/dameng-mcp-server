"""
Main entry point for running the package as a module.

Usage:
    python -m dameng_mcp_server
"""
import asyncio

from dameng_mcp_server.server import main

if __name__ == "__main__":
    asyncio.run(main())
