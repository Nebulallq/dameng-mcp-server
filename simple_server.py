"""
DaMeng MCP Server - Simplified Single-File Version

这是一个简化的单文件版本，适合快速入门和开发测试。
将所有功能集中在一个文件中，便于理解和修改。

使用方法:
1. 设置环境变量或修改代码中的配置
2. 运行: python simple_server.py
3. 或在 Claude Desktop 中配置此脚本
"""

import asyncio
import logging
import os
import sys
from typing import List

# 添加达梦客户端 DLL 路径（在导入 dmPython 之前）
dm_home = os.getenv("DM_HOME")
if dm_home and os.path.exists(dm_home):
    # 将 DM_HOME 添加到 PATH，确保能找到 DLL
    os.environ["PATH"] = dm_home + os.pathsep + os.environ["PATH"]
    
    # 尝试使用 add_dll_directory (Python 3.8+)
    if hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(dm_home)
            print(f"[INFO] 已添加达梦客户端路径: {dm_home}", file=sys.stderr)
        except Exception as e:
            print(f"[WARN] add_dll_directory 失败: {e}", file=sys.stderr)

try:
    from dmPython import connect
except ImportError:
    print("错误: 未找到 dmPython 模块")
    print("请安装: pip install dmPython")
    print("注意: dmPython 需要达梦数据库客户端库支持")
    sys.exit(1)

from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
from pydantic import AnyUrl

# ============== 配置部分 ==============

def get_db_config():
    """
    获取数据库配置
    优先从环境变量读取，否则使用默认值
    """
    config = {
        "user": os.getenv("DAMENG_USER", "SYSDBA"),
        "password": os.getenv("DAMENG_PASSWORD", ""),
        "server": os.getenv("DAMENG_HOST", "localhost"),
        "port": int(os.getenv("DAMENG_PORT", "5236")),
    }

    # 验证必要配置
    if not config["password"]:
        print("警告: DAMENG_PASSWORD 未设置，请设置数据库密码")

    return config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dameng_mcp_server")

# ============== MCP 服务器初始化 ==============

app = Server("dameng_mcp_server")

# ============== 资源处理 ==============

@app.list_resources()
async def list_resources() -> List[Resource]:
    """
    列出达梦数据库中的所有表作为 MCP 资源
    """
    config = get_db_config()
    try:
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT TABLE_NAME FROM ALL_TABLES")
                tables = cursor.fetchall()
                logger.info(f"找到 {len(tables)} 个表")

                resources = []
                for table in tables:
                    resources.append(
                        Resource(
                            uri=f"dameng://{table[0]}/data",
                            name=f"Table: {table[0]}",
                            mimeType="text/plain",
                            description=f"表数据: {table[0]}"
                        )
                    )
                return resources
    except Exception as e:
        logger.error(f"列出资源失败: {str(e)}")
        return []


@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """
    读取表内容作为资源

    URI 格式: dameng://表名/data
    """
    config = get_db_config()
    uri_str = str(uri)
    logger.info(f"读取资源: {uri_str}")

    if not uri_str.startswith("dameng://"):
        raise ValueError(f"无效的 URI 格式: {uri_str}")

    # 从 URI 中提取表名
    parts = uri_str[len("dameng://"):].split('/')
    table_name = parts[0] if parts else ""

    if not table_name:
        raise ValueError(f"无法从 URI 中提取表名: {uri_str}")

    try:
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                # 格式化为 CSV
                result = [",".join(columns)]
                for row in rows:
                    result.append(",".join(map(str, row)))

                return "\n".join(result)

    except Exception as e:
        logger.error(f"读取资源 {uri} 失败: {str(e)}")
        raise RuntimeError(f"读取资源失败: {str(e)}") from e


# ============== 工具定义 ==============

@app.list_tools()
async def list_tools() -> List[Tool]:
    """
    列出所有可用的数据库工具
    """
    logger.info("列出可用工具...")
    return [
        Tool(
            name="execute_sql",
            description="在达梦数据库上执行 SQL 查询。支持 SELECT、INSERT、UPDATE、DELETE 等所有 SQL 语句。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要执行的 SQL 查询语句"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_tables",
            description="列出数据库中的所有表名",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "可选的表名过滤模式（如 'SYS%'）"
                    }
                }
            }
        ),
        Tool(
            name="describe_table",
            description="获取表的详细结构信息，包括列名、数据类型等",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "要描述的表名"
                    }
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="get_schema_info",
            description="获取数据库 Schema 信息，包括用户和对象数量",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "可选的 Schema 过滤模式"
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """
    执行工具调用
    """
    config = get_db_config()
    logger.info(f"调用工具: {name}，参数: {arguments}")

    try:
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                # 根据工具名称执行相应操作
                if name == "execute_sql":
                    return await _execute_sql(cursor, conn, arguments)
                elif name == "list_tables":
                    return await _list_tables(cursor, arguments)
                elif name == "describe_table":
                    return await _describe_table(cursor, arguments)
                elif name == "get_schema_info":
                    return await _get_schema_info(cursor, arguments)
                else:
                    raise ValueError(f"未知工具: {name}")

    except Exception as e:
        logger.error(f"执行工具 '{name}' 失败: {e}")
        return [TextContent(type="text", text=f"错误: {str(e)}")]


# ============== 工具实现 ==============

async def _execute_sql(cursor, conn, arguments: dict) -> List[TextContent]:
    """执行 SQL 查询"""
    query = arguments.get("query", "")
    if not query:
        raise ValueError("query 参数不能为空")

    cursor.execute(query)

    # 如果有结果集（SELECT 查询）
    if cursor.description is not None:
        columns = [desc[0] for desc in cursor.description]
        try:
            rows = cursor.fetchall()
            result = [",".join(columns)]
            for row in rows:
                result.append(",".join(map(str, row)))
            return [TextContent(type="text", text="\n".join(result))]
        except Exception as e:
            return [TextContent(type="text", text=f"查询执行成功，但获取结果失败: {str(e)}")]

    # 非 SELECT 查询
    else:
        conn.commit()
        affected = cursor.rowcount if cursor.rowcount >= 0 else 0
        return [TextContent(type="text", text=f"查询执行成功，影响行数: {affected}")]


async def _list_tables(cursor, arguments: dict) -> List[TextContent]:
    """列出所有表"""
    pattern = arguments.get("pattern", "")

    if pattern:
        cursor.execute(f"SELECT TABLE_NAME FROM ALL_TABLES WHERE TABLE_NAME LIKE '{pattern}'")
    else:
        cursor.execute("SELECT TABLE_NAME FROM ALL_TABLES")

    tables = cursor.fetchall()
    table_names = [t[0] for t in tables]

    return [TextContent(type="text", text="\n".join(table_names) if table_names else "没有找到表")]


async def _describe_table(cursor, arguments: dict) -> List[TextContent]:
    """描述表结构"""
    table_name = arguments.get("table_name", "")
    if not table_name:
        raise ValueError("table_name 参数不能为空")

    cursor.execute(
        f"SELECT COLUMN_NAME, DATA_TYPE, NULLABLE FROM ALL_COLUMNS "
        f"WHERE TABLE_NAME = '{table_name.upper()}'"
    )
    columns = cursor.fetchall()

    if not columns:
        return [TextContent(type="text", text=f"表 '{table_name}' 不存在或没有列")]

    result = [f"表: {table_name}", ""]
    result.append("列名 | 数据类型 | 可空")
    result.append("-" * 50)
    for col in columns:
        result.append(f"{col[0]} | {col[1]} | {col[2]}")

    return [TextContent(type="text", text="\n".join(result))]


async def _get_schema_info(cursor, arguments: dict) -> List[TextContent]:
    """获取 Schema 信息"""
    pattern = arguments.get("pattern", "")

    try:
        if pattern:
            cursor.execute(
                f"SELECT OBJECT_NAME, OWNER FROM ALL_OBJECTS "
                f"WHERE OBJECT_TYPE = 'SCHEMA' AND OBJECT_NAME LIKE '{pattern}'"
            )
        else:
            cursor.execute(
                "SELECT OBJECT_NAME, OWNER FROM ALL_OBJECTS WHERE OBJECT_TYPE = 'SCHEMA'"
            )
    except:
        # 如果查询失败，回退到查询用户
        cursor.execute("SELECT USERNAME, USER_ID FROM ALL_USERS")

    schemas = cursor.fetchall()

    if not schemas:
        return [TextContent(type="text", text="没有找到 Schema")]

    result = ["Schema | Owner", "-" * 30]
    for schema in schemas:
        result.append(f"{schema[0]} | {schema[1]}")

    return [TextContent(type="text", text="\n".join(result))]


# ============== 主程序 ==============

async def main():
    """启动 MCP 服务器"""
    from mcp.server.stdio import stdio_server

    # 显示配置信息
    config = get_db_config()
    print("=" * 50, file=sys.stderr)
    print("启动 DaMeng MCP 服务器...", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print(f"服务器: {config['server']}", file=sys.stderr)
    print(f"端口: {config['port']}", file=sys.stderr)
    print(f"用户: {config['user']}", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    logger.info("启动 DaMeng MCP 服务器...")
    logger.info(f"连接配置: {config['server']}:{config['port']} as {config['user']}")

    async with stdio_server() as (read_stream, write_stream):
        try:
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
        except KeyboardInterrupt:
            logger.info("服务器关闭请求")
        except Exception as e:
            logger.error(f"服务器错误: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
