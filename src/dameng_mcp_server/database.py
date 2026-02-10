"""
Database connection and query handling for DaMeng MCP Server.
"""

import logging
import os
from contextlib import contextmanager
from typing import Any, Generator, List, Optional, Tuple

from dameng_mcp_server.config import DatabaseConfig

logger = logging.getLogger("dameng_mcp_server.database")

# 添加达梦客户端 DLL 路径
dm_home = os.getenv("DM_HOME")
if dm_home and os.path.exists(dm_home):
    # 将 DM_HOME 添加到 PATH，确保能找到 DLL
    os.environ["PATH"] = dm_home + os.pathsep + os.environ["PATH"]
    
    # 尝试使用 add_dll_directory (Python 3.8+)
    if hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(dm_home)
            logger.info(f"已添加达梦客户端路径: {dm_home}")
        except Exception as e:
            logger.warning(f"add_dll_directory 失败: {e}")

from dmPython import Connection, Cursor, connect


class DatabaseManager:
    """Manager for DaMeng database connections."""

    def __init__(self, config: DatabaseConfig):
        """
        Initialize the database manager.

        Args:
            config: Database configuration
        """
        self.config = config

    @contextmanager
    def get_connection(self) -> Generator[Connection, None, None]:
        """
        Get a database connection with context management.

        Yields:
            Connection: A database connection

        Raises:
            RuntimeError: If connection fails
        """
        conn_params = self.config.to_connection_dict()
        logger.debug(f"Connecting to database: {conn_params['server']}:{conn_params['port']}")
        try:
            with connect(**conn_params) as conn:
                yield conn
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise RuntimeError(f"Database connection failed: {str(e)}") from e

    def list_tables(self) -> List[str]:
        """
        List all tables in the database.

        Returns:
            List[str]: List of table names

        Raises:
            RuntimeError: If query fails
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT TABLE_NAME FROM ALL_TABLES")
                    tables = cursor.fetchall()
                    table_names = [table[0] for table in tables]
                    logger.info(f"Found {len(table_names)} tables")
                    return table_names
        except Exception as e:
            logger.error(f"Failed to list tables: {str(e)}")
            raise RuntimeError(f"Failed to list tables: {str(e)}") from e

    def execute_query(
        self, query: str
    ) -> Tuple[Optional[List[str]], Optional[List[Tuple[Any, ...]]], int]:
        """
        Execute a SQL query.

        Args:
            query: SQL query to execute

        Returns:
            Tuple containing:
                - List of column names (if query returns results)
                - List of result rows (if query returns results)
                - Number of rows affected

        Raises:
            RuntimeError: If query execution fails
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)

                    # Handle queries that return result sets
                    if cursor.description is not None:
                        columns = [desc[0] for desc in cursor.description]
                        try:
                            rows = cursor.fetchall()
                            logger.info(f"Query returned {len(rows)} rows")
                            return columns, rows, len(rows)
                        except Exception as e:
                            logger.warning(f"Error fetching results: {str(e)}")
                            return columns, [], 0

                    # Handle non-SELECT queries
                    conn.commit()
                    row_count = cursor.rowcount if cursor.rowcount >= 0 else 0
                    logger.info(f"Query executed successfully. Rows affected: {row_count}")
                    return None, None, row_count

        except Exception as e:
            logger.error(f"Error executing SQL '{query}': {str(e)}")
            raise RuntimeError(f"Error executing query: {str(e)}") from e

    def get_table_info(self, table_name: str) -> List[Tuple[str, str, str]]:
        """
        Get information about a table's columns.

        Args:
            table_name: Name of the table

        Returns:
            List of tuples containing (column_name, data_type, is_nullable)

        Raises:
            RuntimeError: If query fails
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        f"SELECT COLUMN_NAME, DATA_TYPE, NULLABLE FROM ALL_COLUMNS "
                        f"WHERE TABLE_NAME = '{table_name.upper()}'"
                    )
                    columns = cursor.fetchall()
                    return [(col[0], col[1], col[2]) for col in columns]
        except Exception as e:
            logger.error(f"Failed to get table info for '{table_name}': {str(e)}")
            raise RuntimeError(f"Failed to get table info: {str(e)}") from e

    def get_schema_info(self, pattern: Optional[str] = None) -> List[Tuple[str, str, int]]:
        """
        Get information about database schemas.

        Args:
            pattern: Optional pattern to filter schema names

        Returns:
            List of tuples containing (schema_name, owner, object_count)

        Raises:
            RuntimeError: If query fails
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    if pattern:
                        cursor.execute(
                            f"SELECT OBJECT_NAME, OWNER, COUNT(*) as OBJECT_COUNT "
                            f"FROM ALL_OBJECTS "
                            f"WHERE OBJECT_TYPE = 'SCHEMA' AND OBJECT_NAME LIKE '{pattern}' "
                            f"GROUP BY OBJECT_NAME, OWNER"
                        )
                    else:
                        cursor.execute(
                            "SELECT OBJECT_NAME, OWNER, COUNT(*) as OBJECT_COUNT "
                            "FROM ALL_OBJECTS "
                            "WHERE OBJECT_TYPE = 'SCHEMA' "
                            "GROUP BY OBJECT_NAME, OWNER"
                        )
                    schemas = cursor.fetchall()
                    return [(schema[0], schema[1], schema[2]) for schema in schemas]
        except Exception as e:
            logger.error(f"Failed to get schema info: {str(e)}")
            # Fallback: query users/schemas directly
            try:
                with self.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT USERNAME, USER_ID FROM ALL_USERS")
                        users = cursor.fetchall()
                        return [(user[0], user[0], 0) for user in users]
            except Exception as e2:
                logger.error(f"Fallback query also failed: {str(e2)}")
                raise RuntimeError(f"Failed to get schema info: {str(e)}") from e

    def format_query_result(
        self, columns: List[str], rows: List[Tuple[Any, ...]], max_rows: int = 100
    ) -> str:
        """
        Format query results as CSV string.

        Args:
            columns: Column names
            rows: Result rows
            max_rows: Maximum number of rows to format

        Returns:
            str: Formatted results as CSV
        """
        limited_rows = rows[:max_rows]
        result = [",".join(columns)]
        for row in limited_rows:
            result.append(",".join(map(str, row)))
        return "\n".join(result)
