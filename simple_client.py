"""
DaMeng MCP Client - Simplified Single-File Version

这是一个简化的 MCP 客户端，用于连接和测试达梦数据库 MCP 服务器。
支持交互式查询和 AI 对话功能。

使用方法:
1. 确保 MCP 服务器可以运行
2. 配置环境变量（.env 文件）
3. 运行: python simple_client.py
"""

import asyncio
import json
import logging
import os
import re
from contextlib import AsyncExitStack
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dameng_mcp_client")

# 可选: OpenAI 支持（用于 AI 对话功能）
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI 库未安装，AI 对话功能将不可用")


class SimpleDaMengMCPClient:
    """简化的达梦数据库 MCP 客户端"""

    def __init__(self):
        """初始化客户端"""
        self.exit_stack = AsyncExitStack()
        self.session: Optional[ClientSession] = None

        # 尝试初始化 AI 客户端（可选）
        self.ai_client = None
        self.ai_model = None

        if OPENAI_AVAILABLE:
            api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
            if api_key:
                base_url = os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
                model = os.getenv("MODEL", "qwen-max")
                self.ai_client = OpenAI(api_key=api_key, base_url=base_url)
                self.ai_model = model
                logger.info(f"AI 模型已配置: {model}")

        # 输出目录
        self.output_dir = Path("./client_outputs")
        self.output_dir.mkdir(exist_ok=True)

    async def connect_to_server(self, server_script: str = None) -> bool:
        """
        连接到 MCP 服务器

        Args:
            server_script: 服务器脚本路径，默认使用 simple_server.py
        """
        if server_script is None:
            server_script = os.path.join(os.path.dirname(__file__), "simple_server.py")

        # 设置环境变量
        server_env = {
            "DAMENG_HOST": os.getenv("DAMENG_HOST", "localhost"),
            "DAMENG_PORT": os.getenv("DAMENG_PORT", "5236"),
            "DAMENG_USER": os.getenv("DAMENG_USER", "SYSDBA"),
            "DAMENG_PASSWORD": os.getenv("DAMENG_PASSWORD", ""),
        }

        server_params = StdioServerParameters(
            command="python",
            args=[server_script],
            env=server_env,
        )

        try:
            logger.info(f"连接到服务器: {server_script}")

            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio_read, self.stdio_write = stdio_transport

            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio_read, self.stdio_write)
            )

            # 初始化会话
            await self.session.initialize()

            # 获取工具列表
            response = await self.session.list_tools()
            tools = response.tools
            logger.info(f"已连接，支持 {len(tools)} 个工具:")
            for tool in tools:
                logger.info(f"  - {tool.name}")

            return True

        except Exception as e:
            logger.error(f"连接服务器失败: {e}")
            return False

    async def list_resources(self):
        """列出所有可用资源（表）"""
        if not self.session:
            raise RuntimeError("未连接到服务器")

        response = await self.session.list_resources()
        return response.resources

    async def execute_sql(self, query: str) -> str:
        """执行 SQL 查询"""
        if not self.session:
            raise RuntimeError("未连接到服务器")

        result = await self.session.call_tool("execute_sql", {"query": query})
        return result.content[0].text if result.content else "无结果"

    async def list_tables(self, pattern: str = "") -> str:
        """列出数据库表"""
        if not self.session:
            raise RuntimeError("未连接到服务器")

        args = {"pattern": pattern} if pattern else {}
        result = await self.session.call_tool("list_tables", args)
        return result.content[0].text if result.content else "无结果"

    async def describe_table(self, table_name: str) -> str:
        """描述表结构"""
        if not self.session:
            raise RuntimeError("未连接到服务器")

        result = await self.session.call_tool("describe_table", {"table_name": table_name})
        return result.content[0].text if result.content else "无结果"

    async def get_schema_info(self, pattern: str = "") -> str:
        """获取 Schema 信息"""
        if not self.session:
            raise RuntimeError("未连接到服务器")

        args = {"pattern": pattern} if pattern else {}
        result = await self.session.call_tool("get_schema_info", args)
        return result.content[0].text if result.content else "无结果"

    async def close(self):
        """关闭连接"""
        await self.exit_stack.aclose()

    def save_result(self, query: str, result: str):
        """保存查询结果到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = re.sub(r'[\\/:*?"<>|]', '', query[:30])
        filename = f"{safe_name}_{timestamp}.txt"
        file_path = self.output_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"查询: {query}\n\n")
            f.write(f"结果:\n{result}\n")

        logger.info(f"结果已保存: {file_path}")


async def interactive_mode(client: SimpleDaMengMCPClient):
    """交互式查询模式"""
    print("\n" + "=" * 50)
    print("达梦数据库 MCP 客户端 - 交互模式")
    print("=" * 50)
    print("\n可用命令:")
    print("  /sql <查询>      - 执行 SQL 查询")
    print("  /tables [模式]   - 列出表")
    print("  /describe <表名> - 描述表结构")
    print("  /schemas [模式]  - 列出 Schema")
    print("  /resources       - 列出所有资源")
    print("  /quit            - 退出")
    print("\n直接输入 SQL 语句也会自动执行\n")

    while True:
        try:
            user_input = input("\ndameng> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['/quit', 'quit', 'exit', 'q']:
                print("再见!")
                break

            # 处理命令
            if user_input.startswith("/sql "):
                query = user_input[5:]
                result = await client.execute_sql(query)
                print(f"\n结果:\n{result}")
                client.save_result(query, result)

            elif user_input.startswith("/tables"):
                parts = user_input.split(maxsplit=1)
                pattern = parts[1] if len(parts) > 1 else ""
                result = await client.list_tables(pattern)
                print(f"\n表列表:\n{result}")

            elif user_input.startswith("/describe "):
                table_name = user_input[10:]
                result = await client.describe_table(table_name)
                print(f"\n表结构:\n{result}")

            elif user_input.startswith("/schemas"):
                parts = user_input.split(maxsplit=1)
                pattern = parts[1] if len(parts) > 1 else ""
                result = await client.get_schema_info(pattern)
                print(f"\nSchema 信息:\n{result}")

            elif user_input == "/resources":
                resources = await client.list_resources()
                print(f"\n资源列表 (共 {len(resources)} 个):")
                for r in resources[:20]:
                    print(f"  - {r.name}: {r.uri}")
                if len(resources) > 20:
                    print(f"  ... 还有 {len(resources) - 20} 个")

            # 直接执行 SQL
            elif user_input.upper().startswith(("SELECT", "SHOW", "DESCRIBE", "EXPLAIN")):
                result = await client.execute_sql(user_input)
                print(f"\n结果:\n{result}")
                client.save_result(user_input, result)

            else:
                print("未知命令。使用 /quit 退出")

        except KeyboardInterrupt:
            print("\n使用 /quit 退出")
        except Exception as e:
            print(f"\n错误: {e}")
            logger.exception("处理命令时出错")


async def test_mode(client: SimpleDaMengMCPClient):
    """测试模式 - 运行基本测试"""
    print("\n" + "=" * 50)
    print("运行连接测试...")
    print("=" * 50)

    try:
        # 测试 1: 列出表
        print("\n[1/4] 测试列出表...")
        tables = await client.list_tables()
        print(f"[OK] 成功! 找到 {len(tables.splitlines())} 个表")

        # 测试 2: 获取 Schema 信息
        print("\n[2/4] 测试获取 Schema 信息...")
        schemas = await client.get_schema_info()
        print(f"[OK] 成功!")

        # 测试 3: 执行简单查询
        print("\n[3/4] 测试执行查询...")
        result = await client.execute_sql("SELECT COUNT(*) as table_count FROM ALL_TABLES")
        print(f"[OK] 成功! {result}")

        # 测试 4: 列出资源
        print("\n[4/4] 测试列出资源...")
        resources = await client.list_resources()
        print(f"[OK] 成功! 找到 {len(resources)} 个资源")

        print("\n" + "=" * 50)
        print("所有测试通过! [OK]")
        print("=" * 50)

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        logger.exception("测试失败")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="达梦数据库 MCP 客户端")
    parser.add_argument("--test", action="store_true", help="运行测试模式")
    parser.add_argument("--server", help="指定服务器脚本路径")
    args = parser.parse_args()

    client = SimpleDaMengMCPClient()

    try:
        # 检查环境配置
        if not os.getenv("DAMENG_PASSWORD"):
            print("⚠️  警告: DAMENG_PASSWORD 环境变量未设置")
            print("请在 .env 文件中配置数据库连接信息")

        if await client.connect_to_server(args.server):
            if args.test:
                await test_mode(client)
            else:
                await interactive_mode(client)
        else:
            print("无法连接到服务器，请检查配置")
            return 1

        return 0

    finally:
        await client.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code if exit_code is not None else 0)
