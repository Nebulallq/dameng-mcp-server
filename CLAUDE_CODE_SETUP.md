# Claude Code MCP 配置指南

## 如何将达梦数据库 MCP 添加到 Claude Code

### 方法 1: 使用用户配置文件（推荐）

1. **找到 Claude Code 配置文件位置**

   配置文件通常位于用户目录下的 `.claude` 文件夹中。

   可能的位置：
   - Windows: `C:\Users\<用户名>\.claude\config.json`
   - 或: `E:\Users\<用户名>\.claude\config.json`

2. **创建或编辑配置文件**

   如果配置文件不存在，创建一个新的 `config.json`：

   ```json
   {
     "mcpServers": {
       "dameng": {
         "command": "python",
         "args": ["E:\\java project\\dameng-mcp-server\\simple_server.py"],
         "env": {
           "DAMENG_HOST": "10.215.146.129",
           "DAMENG_PORT": "8080",
           "DAMENG_USER": "sqlChiefUser",
           "DAMENG_PASSWORD": "A66XqygMhtHjyHtgqmRkX",
           "DAMENG_DATABASE": "CXNP",
           "DM_HOME": "E:\\Program Files\\PremiumSoft\\dameng_odbc_win",
           "LOG_LEVEL": "INFO"
         }
       }
     }
   }
   ```

### 方法 2: 使用项目配置文件

在项目的 `.claude` 文件夹中创建 `mcp_servers.json`：

```json
{
  "mcpServers": {
    "dameng": {
      "command": "python",
      "args": [
        "${workspaceFolder}/simple_server.py"
      ],
      "env": {
        "DAMENG_HOST": "10.215.146.129",
        "DAMENG_PORT": "8080",
        "DAMENG_USER": "sqlChiefUser",
        "DAMENG_PASSWORD": "A66XqygMhtHjyHtgqmRkX",
        "DAMENG_DATABASE": "CXNP",
        "DM_HOME": "E:\\Program Files\\PremiumSoft\\dameng_odbc_win"
      }
    }
  }
}
```

### 配置说明

| 参数 | 说明 |
|------|------|
| `command` | 运行服务器的命令，这里是 `python` |
| `args` | 服务器脚本路径数组 |
| `env` | 环境变量，包含数据库连接信息 |

### 使用方法

配置完成后，在 Claude Code 中即可使用达梦数据库工具：

**示例对话：**

```
你: 列出 CXNP Schema 中的所有表
Claude: [调用 list_tables 工具]

你: 查看 BASE_DEVICE 表的结构
Claude: [调用 describe_table 工具]

你: 查询 BASE_DEVICE 表的前10条记录
Claude: [调用 execute_sql 工具]
```

### 可用工具

| 工具名 | 功能 | 示例 |
|--------|------|------|
| `execute_sql` | 执行 SQL 查询 | `SELECT * FROM users LIMIT 10` |
| `list_tables` | 列出所有表 | 可选过滤模式 |
| `describe_table` | 查看表结构 | 获取列名和类型 |
| `get_schema_info` | 获取 Schema 信息 | 查看数据库对象 |

### 故障排查

**问题 1: 服务器无法启动**
- 检查 Python 路径是否正确
- 确认 dmPython 已安装
- 检查 DM_HOME 路径是否正确

**问题 2: 连接数据库失败**
- 验证数据库地址和端口
- 检查用户名和密码
- 确认数据库服务正在运行

**问题 3: 找不到配置文件**
- Claude Code 会在用户目录和项目目录查找配置
- 确保文件名是 `config.json` 或 `mcp_servers.json`

### 安全提示

⚠️ **注意**: 配置文件中包含敏感信息（数据库密码），请确保：
1. 不要将包含密码的配置文件提交到 Git
2. 使用 `.gitignore` 排除配置文件
3. 考虑使用环境变量或密钥管理服务

### 测试连接

配置完成后，运行测试脚本验证：

```bash
python simple_client.py --test
```

如果测试通过，说明 MCP 服务器配置正确，可以在 Claude Code 中使用了。
