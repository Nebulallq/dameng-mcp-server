# 达梦数据库 MCP 服务器 - 安装配置指南

本指南将帮助你完成达梦数据库 MCP 服务器的安装和配置。

## 目录

1. [系统要求](#系统要求)
2. [安装达梦数据库客户端](#安装达梦数据库客户端)
3. [安装 Python 依赖](#安装-python-依赖)
4. [配置数据库连接](#配置数据库连接)
5. [运行服务器](#运行服务器)
6. [使用客户端](#使用客户端)
7. [常见问题](#常见问题)

---

## 系统要求

- **Python**: 3.9 或更高版本
- **操作系统**: Windows / Linux / macOS
- **达梦数据库**: 8.0 或更高版本

---

## 安装达梦数据库客户端

### Windows

1. 从达梦官网下载客户端 SDK:
   - 访问: https://www.dameng.com/list_103.html
   - 下载: 达梦数据库客户端 SDK

2. 解压并配置环境变量:
   ```cmd
   # 添加 dmPython 的 DLL 路径到 PATH
   set PATH=%PATH%;C:\dmdbms\bin
   ```

3. 或将以下文件复制到 Python 的 DLLs 目录:
   - `dmdpi.dll`
   - `dmOCI.dll`
   - `dmCrypto.dll`

### Linux

```bash
# 安装达梦客户端库
sudo dpkg -i dmdbms_*.deb  # Debian/Ubuntu
# 或
sudo rpm -ivh dmdbms_*.rpm  # RedHat/CentOS

# 配置库路径
export LD_LIBRARY_PATH=/opt/dmdbms/bin:$LD_LIBRARY_PATH
```

---

## 安装 Python 依赖

### 1. 安装 dmPython

```bash
pip install dmPython
```

如果安装失败，可能需要先安装达梦客户端库。

### 2. 安装项目依赖

```bash
cd "E:\java project\dameng-mcp-server"
pip install -e .
```

或单独安装依赖:

```bash
pip install mcp pydantic python-dotenv
```

### 3. 可选: 安装客户端依赖

如果需要使用 AI 对话功能:

```bash
pip install openai
```

---

## 配置数据库连接

### 方法 1: 使用 .env 文件 (推荐)

在项目根目录创建 `.env` 文件:

```env
# 达梦数据库配置
DAMENG_HOST=localhost
DAMENG_PORT=5236
DAMENG_USER=SYSDBA
DAMENG_PASSWORD=your_password_here
DAMENG_DATABASE=

# 日志配置
LOG_LEVEL=INFO

# AI 配置 (可选)
DASHSCOPE_API_KEY=your_dashscope_api_key
BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL=qwen-max
```

### 方法 2: 系统环境变量

```bash
# Windows
set DAMENG_HOST=localhost
set DAMENG_PORT=5236
set DAMENG_USER=SYSDBA
set DAMENG_PASSWORD=your_password

# Linux/macOS
export DAMENG_HOST=localhost
export DAMENG_PORT=5236
export DAMENG_USER=SYSDBA
export DAMENG_PASSWORD=your_password
```

---

## 运行服务器

### 方法 1: 运行简化版服务器

```bash
cd "E:\java project\dameng-mcp-server"
python simple_server.py
```

### 方法 2: 运行模块化服务器

```bash
python -m dameng_mcp_server
```

### 方法 3: 在 Claude Desktop 中使用

编辑 Claude Desktop 配置文件:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "dameng": {
      "command": "python",
      "args": ["E:\\java project\\dameng-mcp-server\\simple_server.py"],
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

---

## 使用客户端

### 交互式客户端

```bash
python simple_client.py
```

可用命令:
- `/sql <查询>` - 执行 SQL 查询
- `/tables [模式]` - 列出表
- `/describe <表名>` - 描述表结构
- `/schemas [模式]` - 列出 Schema
- `/resources` - 列出所有资源
- `/quit` - 退出

### 测试模式

```bash
python simple_client.py --test
```

---

## 常见问题

### 问题 1: ImportError: DLL load failed while importing dmPython

**原因**: dmPython 无法找到达梦数据库的客户端库

**解决方案**:
1. 确保已安装达梦数据库客户端 SDK
2. 将达梦的 bin 目录添加到系统 PATH
3. 或将所需的 DLL 文件复制到 Python 的 DLLs 目录

### 问题 2: Connection refused

**原因**: 无法连接到达梦数据库服务器

**解决方案**:
1. 检查达梦数据库是否正在运行
2. 检查 host 和 port 配置是否正确
3. 检查防火墙设置

### 问题 3: Authentication failed

**原因**: 用户名或密码错误

**解决方案**:
1. 检查 .env 文件中的用户名和密码
2. 确认使用的是正确的用户名（默认: SYSDBA）

### 问题 4: Module 'mcp' not found

**原因**: MCP 库未安装

**解决方案**:
```bash
pip install mcp
```

### 问题 5: 列表为空或查询无结果

**原因**: 可能是权限问题或表不存在

**解决方案**:
1. 确认用户有足够的权限访问系统表
2. 尝试使用不同的查询
3. 检查日志以获取更多信息

---

## 项目结构

```
dameng-mcp-server/
├── simple_server.py          # 简化版服务器 (单文件)
├── simple_client.py          # 简化版客户端 (单文件)
├── src/
│   └── dameng_mcp_server/
│       ├── server.py         # 模块化服务器
│       ├── database.py       # 数据库管理
│       ├── tools.py          # 工具定义
│       └── config.py         # 配置管理
├── examples/
│   ├── basic_client.py       # 基础客户端示例
│   └── mcp_client.py         # 完整客户端
├── tests/
│   └── test_server.py        # 服务器测试
├── .env.example              # 环境变量示例
├── INSTALL_GUIDE.md          # 本指南
└── README.md                 # 项目说明
```

---

## 可用工具

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `execute_sql` | 执行 SQL 查询 | `query` (必填) |
| `list_tables` | 列出所有表 | `pattern` (可选) |
| `describe_table` | 描述表结构 | `table_name` (必填) |
| `get_schema_info` | 获取 Schema 信息 | `pattern` (可选) |

---

## 可用资源

数据库表以资源形式暴露:

```
dameng://{table_name}/data
```

例如:
```
dameng://SYSUSER/data
```

---

## 开发和调试

### 启用调试日志

在 `.env` 文件中设置:
```env
LOG_LEVEL=DEBUG
```

### 运行测试

```bash
pytest tests/ -v
```

### 代码检查

```bash
# 格式化代码
black src/
isort src/

# 类型检查
mypy src/
```

---

## 下一步

- 查看 [README.md](README.md) 了解更多功能
- 查看 [examples/](examples/) 目录中的示例代码
- 加入社区讨论和分享经验

---

## 获取帮助

如果遇到问题:
1. 检查本指南的常见问题部分
2. 查看 GitHub Issues
3. 达梦数据库官方文档: https://www.dameng.com/
