# DaMeng MCP Server 调试指南

## 快速调试

运行调试脚本进行快速诊断：

```bash
python debug.py
```

该脚本会自动检查：
- Python 版本
- 依赖包安装情况
- 环境变量配置
- 数据库连接
- 项目结构完整性

---

## 1. 环境检查

### 检查 Python 版本

```bash
python --version
# 或
python3 --version
```

**要求**: Python 3.9 或更高版本

### 检查依赖包

```bash
pip list | grep -E "(mcp|dmPython|pydantic)"
```

**必需的包**:
- `mcp` >= 0.9.0
- `dmPython` >= 2.3.0
- `pydantic` >= 2.0.0
- `python-dotenv` >= 1.0.0

**安装依赖**:

```bash
pip install -r requirements.txt
```

---

## 2. 数据库连接调试

### 测试 dmPython 连接

创建测试脚本 `test_db.py`:

```python
import os
from dotenv import load_dotenv
from dmPython import connect

load_dotenv()

config = {
    "user": os.getenv("DAMENG_USER", "SYSDBA"),
    "password": os.getenv("DAMENG_PASSWORD"),
    "server": os.getenv("DAMENG_HOST", "localhost"),
    "port": int(os.getenv("DAMENG_PORT", "5236")),
}

try:
    print(f"连接到 {config['server']}:{config['port']} ...")
    conn = connect(**config)
    print("✅ 连接成功!")

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM V$TABLES LIMIT 5")
    tables = cursor.fetchall()
    print(f"发现 {len(tables)} 个表")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ 连接失败: {e}")
```

运行测试:

```bash
python test_db.py
```

---

## 3. 服务器启动调试

### 启用详细日志

设置环境变量启用 DEBUG 日志:

```bash
# Linux/Mac
export LOG_LEVEL=DEBUG
python -m dameng_mcp_server

# Windows
set LOG_LEVEL=DEBUG
python -m dameng_mcp_server
```

### 检查服务器输出

服务器启动时会在 stderr 输出配置信息:

```
Starting DaMeng MCP server...
Server: localhost
Port: 5236
User: SYSDBA
Schema: (default)
```

### 常见启动问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `ModuleNotFoundError: No module named 'mcp'` | mcp 未安装 | `pip install mcp` |
| `ModuleNotFoundError: No module named 'dmPython'` | dmPython 未安装 | `pip install dmPython` |
| `ValueError: Missing required database configuration` | .env 文件未配置 | 创建 .env 文件并设置 DAMENG_PASSWORD |
| `RuntimeError: Database connection failed` | 数据库连接失败 | 检查主机、端口、用户名、密码 |

---

## 4. 使用 Claude Desktop 调试

### 查看 Claude Desktop 日志

**Windows**: `%APPDATA%\Claude\logs\`
**macOS**: `~/Library/Logs/Claude/`

### 配置文件位置

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**示例配置**:

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
        "DAMENG_PASSWORD": "your_password",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

---

## 5. 客户端调试

### 运行基本客户端

```bash
cd examples
python basic_client.py
```

### 运行交互式客户端

```bash
cd examples
python mcp_client.py
```

### 客户端命令

| 命令 | 功能 |
|------|------|
| `/sql <query>` | 直接执行 SQL |
| `/tables [pattern]` | 列出表 |
| `/describe <table>` | 描述表结构 |
| `/schemas [pattern]` | 列出 Schema |
| `/quit` | 退出 |

---

## 6. 日志分析

### 日志级别

| 级别 | 用途 |
|------|------|
| DEBUG | 详细的调试信息 |
| INFO | 一般信息（默认） |
| WARNING | 警告信息 |
| ERROR | 错误信息 |

### 设置日志级别

在 `.env` 文件中:

```env
LOG_LEVEL=DEBUG
```

---

## 7. 单元测试

运行测试套件:

```bash
pytest tests/ -v
```

运行特定测试:

```bash
pytest tests/test_server.py -v
```

运行集成测试（需要真实数据库）:

```bash
pytest tests/ -v -m integration
```

---

## 8. 常见问题排查

### 问题: 找不到 dmPython

```bash
# 检查是否安装
python -c "import dmPython; print(dmPython.__file__)"

# 重新安装
pip uninstall dmPython
pip install dmPython
```

### 问题: 连接超时

```bash
# 测试端口是否开放
telnet localhost 5236

# 检查达梦服务状态
# Linux
systemctl status DmService
# Windows
sc query DmService
```

### 问题: 权限不足

确保数据库用户有足够权限:

```sql
-- 检查当前用户
SELECT USER FROM DUAL;

-- 检查表权限
SELECT * FROM ALL_TABLES WHERE OWNER = 'YOUR_USER';
```

---

## 9. 开发模式调试

### 使用 pdb 调试

在代码中插入断点:

```python
import pdb; pdb.set_trace()
```

### 使用 VSCode 调试

创建 `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "DaMeng MCP Server",
      "type": "python",
      "request": "launch",
      "module": "dameng_mcp_server",
      "env": {
        "DAMENG_HOST": "localhost",
        "DAMENG_PORT": "5236",
        "DAMENG_USER": "SYSDBA",
        "DAMENG_PASSWORD": "your_password",
        "LOG_LEVEL": "DEBUG"
      }
    }
  ]
}
```

---

## 10. 获取帮助

如果问题仍未解决:

1. 检查 [达梦数据库官方文档](https://www.dameng.com/)
2. 查看 [MCP 协议文档](https://modelcontextprotocol.io/)
3. 提交 Issue 到项目仓库
