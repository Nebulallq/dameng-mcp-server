"""
Configuration management for DaMeng MCP Server.
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    user: str
    password: str
    server: str
    port: int
    schema: str

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """
        Create configuration from environment variables.

        Returns:
            DatabaseConfig: The database configuration

        Raises:
            ValueError: If required environment variables are missing
        """
        user = os.getenv("DAMENG_USER", "SYSDBA")
        password = os.getenv("DAMENG_PASSWORD", "")
        server = os.getenv("DAMENG_HOST", "localhost")
        port = int(os.getenv("DAMENG_PORT", "5236"))
        schema = os.getenv("DAMENG_DATABASE", "")

        if not password:
            raise ValueError(
                "Missing required database configuration. "
                "DAMENG_PASSWORD environment variable is required"
            )

        return cls(
            user=user,
            password=password,
            server=server,
            port=port,
            schema=schema,
        )

    def to_connection_dict(self) -> dict:
        """
        Convert to connection dictionary for dmPython.

        Returns:
            dict: Connection parameters
        """
        return {
            "user": self.user,
            "password": self.password,
            "server": self.server,
            "port": self.port,
        }


@dataclass
class ServerConfig:
    """MCP Server configuration."""

    log_level: str
    db_config: DatabaseConfig

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """
        Create server configuration from environment variables.

        Returns:
            ServerConfig: The server configuration
        """
        log_level = os.getenv("LOG_LEVEL", "INFO")
        db_config = DatabaseConfig.from_env()

        return cls(log_level=log_level, db_config=db_config)

    def setup_logging(self) -> None:
        """Configure logging based on the log level setting."""
        numeric_level = getattr(logging, self.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
