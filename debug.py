"""
DaMeng MCP Server 调试脚本

用于检测环境和连接问题的调试工具
"""

import os
import sys
from pathlib import Path

def print_section(title: str):
    """打印分隔的标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check_python_version():
    """检查 Python 版本"""
    print_section("1. Python 版本检查")
    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    print(f"Python 路径: {sys.executable}")

    if version.major == 3 and version.minor >= 9:
        print("✅ Python 版本符合要求 (>= 3.9)")
        return True
    else:
        print("❌ Python 版本不符合要求，需要 3.9+")
        return False


def check_dependencies():
    """检查依赖包"""
    print_section("2. 依赖包检查")

    packages = {
        "mcp": "MCP 协议库",
        "dmPython": "达梦数据库驱动",
        "pydantic": "数据验证库",
        "dotenv": "python-dotenv",
        "openai": "OpenAI 客户端（可选）"
    }

    missing = []
    installed = []

    for package, desc in packages.items():
        try:
            if package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package)
            print(f"✅ {package:15} - {desc}")
            installed.append(package)
        except ImportError:
            print(f"❌ {package:15} - {desc} [未安装]")
            missing.append(package)

    if missing:
        print(f"\n⚠️  缺失 {len(missing)} 个依赖包")
        print(f"安装命令: pip install {' '.join(missing)}")

    return len(missing) == 0


def check_env_config():
    """检查环境变量配置"""
    print_section("3. 环境变量配置")

    from dotenv import load_dotenv
    load_dotenv()

    env_vars = {
        "DAMENG_HOST": "数据库主机",
        "DAMENG_PORT": "数据库端口",
        "DAMENG_USER": "数据库用户",
        "DAMENG_PASSWORD": "数据库密码",
        "DAMENG_DATABASE": "数据库名称（可选）",
        "LOG_LEVEL": "日志级别（可选）"
    }

    all_set = True

    for var, desc in env_vars.items():
        value = os.getenv(var)
        if value:
            if "PASSWORD" in var:
                print(f"✅ {var:20} = ******** ({desc})")
            else:
                print(f"✅ {var:20} = {value} ({desc})")
        else:
            required = "DATABASE" not in var and "LOG_LEVEL" not in var
            if required:
                print(f"❌ {var:20} - {desc} [未设置]")
                all_set = False
            else:
                print(f"⚪ {var:20} - {desc} [可选]")

    return all_set


def check_db_connection():
    """检查数据库连接"""
    print_section("4. 数据库连接测试")

    try:
        from dotenv import load_dotenv
        load_dotenv()

        config = {
            "user": os.getenv("DAMENG_USER", "SYSDBA"),
            "password": os.getenv("DAMENG_PASSWORD", ""),
            "server": os.getenv("DAMENG_HOST", "localhost"),
            "port": int(os.getenv("DAMENG_PORT", "5236")),
        }

        print(f"尝试连接: {config['server']}:{config['port']}")

        import dmPython
        print(f"✅ dmPython 版本: {dmPython.__version__ if hasattr(dmPython, '__version__') else 'unknown'}")

        conn = dmPython.connect(**config)
        print("✅ 数据库连接成功!")

        # 测试查询
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM V$TABLES LIMIT 5")
        tables = cursor.fetchall()
        print(f"✅ 查询测试成功! 发现 {len(tables)} 个表")

        cursor.close()
        conn.close()

        return True

    except ImportError as e:
        print(f"❌ dmPython 未安装: {e}")
        return False
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def check_project_structure():
    """检查项目结构"""
    print_section("5. 项目结构检查")

    project_dir = Path(__file__).parent
    src_dir = project_dir / "src" / "dameng_mcp_server"

    required_files = [
        "server.py",
        "config.py",
        "database.py",
        "tools.py",
        "__init__.py"
    ]

    all_exist = True
    for file in required_files:
        file_path = src_dir / file
        if file_path.exists():
            print(f"✅ src/dameng_mcp_server/{file}")
        else:
            print(f"❌ src/dameng_mcp_server/{file} [缺失]")
            all_exist = False

    return all_exist


def main():
    """主函数"""
    print("\n" + "🔍" * 30)
    print("  DaMeng MCP Server 调试工具")
    print("🔍" * 30)

    results = {
        "Python 版本": check_python_version(),
        "依赖包": check_dependencies(),
        "环境变量": check_env_config(),
        "数据库连接": False,  # 默认为 False，只在配置完整时测试
        "项目结构": check_project_structure()
    }

    # 只在配置完整时测试数据库连接
    if results["环境变量"] and results["依赖包"]:
        results["数据库连接"] = check_db_connection()

    # 总结
    print_section("调试总结")
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:15} {status}")

    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 所有检查通过！可以启动服务器了")
        print("\n启动命令:")
        print("  python -m dameng_mcp_server")
        print("\n或运行客户端:")
        print("  cd examples")
        print("  python mcp_client.py")
    else:
        print("\n⚠️  请先解决上述问题")
        if not results["依赖包"]:
            print("\n安装依赖:")
            print("  pip install -r requirements.txt")
        if not results["环境变量"]:
            print("\n配置 .env 文件:")
            print("  cp .env.example .env")
            print("  然后编辑 .env 文件填写数据库信息")


if __name__ == "__main__":
    main()
