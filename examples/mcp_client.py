"""
DaMeng MCP Client - 完整的客户端实现

该客户端可以：
1. 连接到 DaMeng MCP 服务器
2. 列出可用的工具和资源
3. 执行 SQL 查询
4. 与 AI 模型对话，自动调用工具
5. 保存对话历史
"""

import asyncio
import json
import logging
import os
import re
from contextlib import AsyncExitStack
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dameng_mcp_client")


class DaMengMCPClient:
    """DaMeng MCP 客户端类。"""

    def __init__(self):
        """初始化客户端。"""
        self.exit_stack = AsyncExitStack()
        self.session: Optional[ClientSession] = None
        self.server_params: Optional[StdioServerParameters] = None

        # OpenAI 配置
        api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        model = os.getenv("MODEL", "qwen-max")

        if not api_key:
            logger.warning("未找到 API Key，将使用基本模式（无 AI 增强）")
            self.client = None
            self.model = None
        else:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            self.model = model
            logger.info(f"已配置 AI 模型: {model}")

        # 输出目录
        self.output_dir = Path("./mcp_outputs")
        self.output_dir.mkdir(exist_ok=True)

    async def connect_to_server(self, server_script_path: str = None) -> bool:
        """
        连接到 MCP 服务器。

        Args:
            server_script_path: 服务器脚本路径，默认使用项目中的服务器

        Returns:
            bool: 连接是否成功
        """
        if server_script_path is None:
            # 使用默认的服务器模块
            server_script_path = "-m"
            server_args = ["dameng_mcp_server"]
        else:
            server_args = [server_script_path]

        # 设置环境变量
        server_env = {
            "DAMENG_HOST": os.getenv("DAMENG_HOST", "localhost"),
            "DAMENG_PORT": os.getenv("DAMENG_PORT", "5236"),
            "DAMENG_USER": os.getenv("DAMENG_USER", "SYSDBA"),
            "DAMENG_PASSWORD": os.getenv("DAMENG_PASSWORD", ""),
        }

        self.server_params = StdioServerParameters(
            command="python",
            args=server_args,
            env=server_env,
        )

        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(self.server_params)
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
            logger.info(f"已连接到服务器，支持 {len(tools)} 个工具:")
            for tool in tools:
                logger.info(f"  - {tool.name}: {tool.description}")

            return True

        except Exception as e:
            logger.error(f"连接服务器失败: {e}")
            return False

    async def list_resources(self) -> list:
        """列出所有可用的资源。"""
        if not self.session:
            raise RuntimeError("未连接到服务器")

        response = await self.session.list_resources()
        return response.resources

    async def execute_sql(self, query: str) -> str:
        """
        执行 SQL 查询。

        Args:
            query: SQL 查询语句

        Returns:
            str: 查询结果
        """
        if not self.session:
            raise RuntimeError("未连接到服务器")

        result = await self.session.call_tool("execute_sql", {"query": query})
        return result.content[0].text if result.content else "无结果"

    async def list_tables(self, pattern: str = None) -> str:
        """
        列出数据库中的表。

        Args:
            pattern: 可选的表名过滤模式

        Returns:
            str: 表列表
        """
        if not self.session:
            raise RuntimeError("未连接到服务器")

        args = {"pattern": pattern} if pattern else {}
        result = await self.session.call_tool("list_tables", args)
        return result.content[0].text if result.content else "无结果"

    async def describe_table(self, table_name: str) -> str:
        """
        描述表结构。

        Args:
            table_name: 表名

        Returns:
            str: 表结构信息
        """
        if not self.session:
            raise RuntimeError("未连接到服务器")

        result = await self.session.call_tool("describe_table", {"table_name": table_name})
        return result.content[0].text if result.content else "无结果"

    async def get_schema_info(self, pattern: str = None) -> str:
        """
        获取 Schema 信息。

        Args:
            pattern: 可选的 Schema 过滤模式

        Returns:
            str: Schema 信息
        """
        if not self.session:
            raise RuntimeError("未连接到服务器")

        args = {"schema_pattern": pattern} if pattern else {}
        result = await self.session.call_tool("get_schema_info", args)
        return result.content[0].text if result.content else "无结果"

    async def plan_tool_usage(self, query: str, tools: list) -> list:
        """
        使用 AI 规划工具调用顺序。

        Args:
            query: 用户查询
            tools: 可用工具列表

        Returns:
            list: 工具调用计划
        """
        if not self.client:
            # 无 AI 时返回简单计划
            return []

        system_prompt = {
            "role": "system",
            "content": (
                "你是一个数据库助手规划器。根据用户的查询，决定需要调用哪些数据库工具。\n"
                "可用工具:\n"
                "- list_tables: 列出数据库中的表\n"
                "- describe_table: 获取表的结构信息\n"
                "- execute_sql: 执行 SQL 查询\n"
                "- get_schema_info: 获取 Schema 信息\n\n"
                "请以 JSON 数组格式返回调用计划，每个元素包含:\n"
                '- {"name": "tool_name", "arguments": {...}}\n\n'
                "不要返回自然语言，只返回 JSON。"
            )
        }

        planning_messages = [
            system_prompt,
            {"role": "user", "content": query}
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=planning_messages,
            )

            content = response.choices[0].message.content.strip()
            match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", content)
            if match:
                json_text = match.group(1)
            else:
                json_text = content

            plan = json.loads(json_text)
            return plan if isinstance(plan, list) else []

        except Exception as e:
            logger.warning(f"AI 规划失败: {e}，使用默认行为")
            return []

    async def process_query(self, query: str) -> str:
        """
        处理用户查询。

        Args:
            query: 用户查询内容

        Returns:
            str: 处理结果
        """
        if not self.session:
            raise RuntimeError("未连接到服务器")

        messages = [{"role": "user", "content": query}]
        response = await self.session.list_tools()

        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            for tool in response.tools
        ]

        # 获取工具调用计划
        tool_plan = await self.plan_tool_usage(query, available_tools)

        tool_outputs = {}
        messages = [{"role": "user", "content": query}]

        # 执行工具调用
        for step in tool_plan:
            tool_name = step.get("name")
            tool_args = step.get("arguments", {})

            # 解析引用
            for key, val in tool_args.items():
                if isinstance(val, str) and val.startswith("{{") and val.endswith("}}"):
                    ref_key = val.strip("{} ")
                    tool_args[key] = tool_outputs.get(ref_key, val)

            try:
                result = await self.session.call_tool(tool_name, tool_args)
                tool_outputs[tool_name] = result.content[0].text
                messages.append({
                    "role": "tool",
                    "tool_name": tool_name,
                    "content": result.content[0].text
                })
            except Exception as e:
                logger.error(f"工具调用失败 {tool_name}: {e}")
                tool_outputs[tool_name] = f"错误: {str(e)}"

        # 如果有 AI，生成最终回复
        if self.client:
            try:
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
                final_output = final_response.choices[0].message.content
            except Exception as e:
                logger.error(f"AI 生成回复失败: {e}")
                final_output = str(tool_outputs)
        else:
            final_output = str(tool_outputs)

        # 保存对话记录
        await self.save_conversation(query, final_output)

        return final_output

    async def save_conversation(self, query: str, response: str) -> str:
        """
        保存对话记录到文件。

        Args:
            query: 用户查询
            response: AI 响应

        Returns:
            str: 保存的文件路径
        """
        def clean_filename(text: str) -> str:
            text = text.strip()
            text = re.sub(r'[\\/:*?"<>|]', '', text)
            return text[:50]

        safe_filename = clean_filename(query)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_filename}_{timestamp}.txt"
        file_path = self.output_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"用户提问: {query}\n\n")
            f.write(f"AI 回复:\n{response}\n")

        logger.info(f"对话记录已保存: {file_path}")
        return str(file_path)

    async def chat_loop(self):
        """交互式聊天循环。"""
        if not self.session:
            raise RuntimeError("请先连接到服务器")

        print("\n🤖 DaMeng MCP 客户端已启动！")
        print("命令:")
        print("  直接输入问题 - 与 AI 对话")
        print("  /sql <查询> - 直接执行 SQL")
        print("  /tables [模式] - 列出表")
        print("  /describe <表名> - 描述表")
        print("  /schemas [模式] - 列出 Schema")
        print("  /quit - 退出\n")

        while True:
            try:
                user_input = input("\n你> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['/quit', 'quit', 'exit']:
                    print("再见！")
                    break

                # 处理命令
                if user_input.startswith("/sql "):
                    query = user_input[5:]
                    result = await self.execute_sql(query)
                    print(f"\n结果:\n{result}")

                elif user_input.startswith("/tables"):
                    parts = user_input.split(maxsplit=1)
                    pattern = parts[1] if len(parts) > 1 else None
                    result = await self.list_tables(pattern)
                    print(f"\n表列表:\n{result}")

                elif user_input.startswith("/describe "):
                    table_name = user_input[10:]
                    result = await self.describe_table(table_name)
                    print(f"\n表结构:\n{result}")

                elif user_input.startswith("/schemas"):
                    parts = user_input.split(maxsplit=1)
                    pattern = parts[1] if len(parts) > 1 else None
                    result = await self.get_schema_info(pattern)
                    print(f"\nSchema 信息:\n{result}")

                else:
                    # AI 对话模式
                    response = await self.process_query(user_input)
                    print(f"\n🤖 AI: {response}")

            except KeyboardInterrupt:
                print("\n使用 /quit 退出")
            except Exception as e:
                logger.error(f"处理错误: {e}")

    async def close(self):
        """关闭客户端连接。"""
        await self.exit_stack.aclose()


async def main():
    """主函数。"""
    client = DaMengMCPClient()

    try:
        if await client.connect_to_server():
            await client.chat_loop()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
