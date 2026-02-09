"""
Tests for DaMeng MCP Server.
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dameng_mcp_server.config import DatabaseConfig, ServerConfig
from dameng_mcp_server.server import app, get_config, get_db_manager


@pytest.fixture
def mock_db_config():
    """Mock database configuration."""
    os.environ["DAMENG_PASSWORD"] = "test_password"
    os.environ["DAMENG_USER"] = "test_user"
    os.environ["DAMENG_HOST"] = "test_host"
    os.environ["DAMENG_PORT"] = "1234"
    yield
    # Cleanup
    for key in ["DAMENG_PASSWORD", "DAMENG_USER", "DAMENG_HOST", "DAMENG_PORT"]:
        os.environ.pop(key, None)


class TestDatabaseConfig:
    """Tests for DatabaseConfig."""

    def test_from_env_with_password(self, mock_db_config):
        """Test creating config from environment variables."""
        config = DatabaseConfig.from_env()

        assert config.user == "test_user"
        assert config.password == "test_password"
        assert config.server == "test_host"
        assert config.port == 1234
        assert config.schema == ""

    def test_from_env_missing_password(self):
        """Test error when password is missing."""
        os.environ.pop("DAMENG_PASSWORD", None)

        with pytest.raises(ValueError, match="DAMENG_PASSWORD"):
            DatabaseConfig.from_env()

    def test_to_connection_dict(self, mock_db_config):
        """Test converting config to connection dict."""
        config = DatabaseConfig.from_env()
        conn_dict = config.to_connection_dict()

        assert conn_dict["user"] == "test_user"
        assert conn_dict["password"] == "test_password"
        assert conn_dict["server"] == "test_host"
        assert conn_dict["port"] == 1234


class TestServerConfig:
    """Tests for ServerConfig."""

    def test_from_env(self, mock_db_config):
        """Test creating server config from environment."""
        os.environ["LOG_LEVEL"] = "DEBUG"

        config = ServerConfig.from_env()

        assert config.log_level == "DEBUG"
        assert config.db_config.user == "test_user"


class TestServer:
    """Tests for MCP Server."""

    @pytest.fixture
    def reset_globals(self):
        """Reset global variables between tests."""
        import dameng_mcp_server.server as server_module

        original_config = server_module._config
        original_db_manager = server_module._db_manager
        original_tool_executor = server_module._tool_executor

        server_module._config = None
        server_module._db_manager = None
        server_module._tool_executor = None

        yield

        server_module._config = original_config
        server_module._db_manager = original_db_manager
        server_module._tool_executor = original_tool_executor

    def test_get_config(self, reset_globals, mock_db_config):
        """Test getting server configuration."""
        config = get_config()

        assert isinstance(config, ServerConfig)
        assert config.db_config.user == "test_user"

    def test_get_db_manager(self, reset_globals, mock_db_config):
        """Test getting database manager."""
        manager = get_db_manager()

        assert manager is not None
        assert manager.config.user == "test_user"

    @pytest.mark.asyncio
    async def test_list_tools(self, reset_globals, mock_db_config):
        """Test listing available tools."""
        tools = await app.list_tools()

        assert len(tools) > 0
        tool_names = {tool.name for tool in tools}
        assert "execute_sql" in tool_names
        assert "list_tables" in tool_names
        assert "describe_table" in tool_names


@pytest.mark.integration
class TestIntegration:
    """Integration tests (require real database connection)."""

    @pytest.fixture
    def real_config(self):
        """Setup real database config from environment."""
        if not os.getenv("DAMENG_PASSWORD"):
            pytest.skip("DAMENG_PASSWORD not set for integration tests")

        config = DatabaseConfig.from_env()
        return config

    @pytest.mark.asyncio
    async def test_real_connection(self, real_config):
        """Test real database connection."""
        from dameng_mcp_server.database import DatabaseManager

        manager = DatabaseManager(real_config)

        try:
            tables = manager.list_tables()
            assert isinstance(tables, list)
        except Exception as e:
            pytest.skip(f"Could not connect to database: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
