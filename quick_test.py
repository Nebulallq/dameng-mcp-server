"""
达梦数据库 MCP 服务器 - 快速测试脚本

此脚本用于快速验证安装和配置是否正确。
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(text):
    """打印步骤"""
    print(f"\n[+] {text}")


def print_success(text):
    """打印成功信息"""
    print(f"[OK] {text}")


def print_error(text):
    """打印错误信息"""
    print(f"[FAIL] {text}")


def print_warning(text):
    """打印警告信息"""
    print(f"[WARN] {text}")


def check_python_version():
    """检查 Python 版本"""
    print_step("检查 Python 版本...")
    version = sys.version_info
    if version >= (3, 9):
        print_success(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python 版本过低: {version.major}.{version.minor}.{version.micro}")
        print_warning("需要 Python 3.9 或更高版本")
        return False


def check_dependencies():
    """检查依赖包"""
    print_step("检查 Python 依赖包...")

    required = [
        ("mcp", "MCP 协议库"),
        ("dmPython", "达梦数据库驱动"),
        ("pydantic", "数据验证库"),
        ("dotenv", "环境变量管理"),
    ]

    optional = [
        ("openai", "OpenAI 客户端 (可选)"),
    ]

    all_ok = True

    print("\n必需依赖:")
    for module, desc in required:
        try:
            __import__(module)
            print_success(f"{module} - {desc}")
        except ImportError:
            print_error(f"{module} - {desc} [未安装]")
            all_ok = False

    print("\n可选依赖:")
    for module, desc in optional:
        try:
            __import__(module)
            print_success(f"{module} - {desc}")
        except ImportError:
            print_warning(f"{module} - {desc} [未安装]")

    return all_ok


def check_env_config():
    """检查环境配置"""
    print_step("检查环境配置...")

    from dotenv import load_dotenv
    load_dotenv()

    required_vars = [
        ("DAMENG_HOST", "localhost", "数据库主机"),
        ("DAMENG_PORT", "5236", "数据库端口"),
        ("DAMENG_USER", "SYSDBA", "数据库用户"),
        ("DAMENG_PASSWORD", None, "数据库密码"),
    ]

    all_ok = True
    config = {}

    for var, default, desc in required_vars:
        value = os.getenv(var, default)
        if value:
            config[var] = value
            if var == "DAMENG_PASSWORD":
                print_success(f"{var} = *** ({desc})")
            else:
                print_success(f"{var} = {value} ({desc})")
        else:
            print_error(f"{var} 未设置 ({desc})")
            all_ok = False

    return all_ok, config


def check_dmclient():
    """检查达梦客户端库"""
    print_step("检查达梦客户端库...")

    try:
        from dmPython import connect
        print_success("dmPython 可以导入")

        # 尝试导入 dmPython 的底层模块
        try:
            import dmPython
            print_success(f"dmPython 版本: {getattr(dmPython, '__version__', '未知')}")
        except:
            pass

        return True

    except ImportError as e:
        print_error(f"dmPython 导入失败: {e}")
        print_warning("请确保已安装达梦数据库客户端 SDK")
        return False

    except Exception as e:
        print_error(f"dmPython 加载错误: {e}")
        if "DLL" in str(e) or "library" in str(e):
            print_warning("这可能是因为达梦客户端库未正确安装")
            print_warning("请参考 INSTALL_GUIDE.md 配置达梦客户端")
        return False


def check_database_connection(config):
    """检查数据库连接"""
    print_step("测试数据库连接...")

    try:
        from dmPython import connect

        conn_params = {
            "user": config.get("DAMENG_USER", "SYSDBA"),
            "password": config.get("DAMENG_PASSWORD", ""),
            "server": config.get("DAMENG_HOST", "localhost"),
            "port": int(config.get("DAMENG_PORT", "5236")),
        }

        print(f"连接信息:")
        print(f"  主机: {conn_params['server']}")
        print(f"  端口: {conn_params['port']}")
        print(f"  用户: {conn_params['user']}")

        with connect(**conn_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM ALL_TABLES")
                count = cursor.fetchone()[0]
                print_success(f"连接成功! 数据库中有 {count} 个表")
                return True

    except Exception as e:
        print_error(f"连接失败: {e}")
        return False


def check_server_files():
    """检查服务器文件"""
    print_step("检查项目文件...")

    files = [
        ("simple_server.py", "简化版服务器"),
        ("simple_client.py", "简化版客户端"),
        ("src/dameng_mcp_server/server.py", "模块化服务器"),
    ]

    all_ok = True
    for file_path, desc in files:
        if os.path.exists(file_path):
            print_success(f"{file_path} - {desc}")
        else:
            print_warning(f"{file_path} - {desc} [未找到]")
            if "simple" in file_path:
                all_ok = False

    return all_ok


def main():
    """主测试流程"""
    print_header("达梦数据库 MCP 服务器 - 安装验证")

    results = {}

    # 1. Python 版本
    results["python"] = check_python_version()

    # 2. 依赖包
    results["dependencies"] = check_dependencies()

    # 3. 项目文件
    results["files"] = check_server_files()

    # 4. 达梦客户端库
    results["dmclient"] = check_dmclient()

    # 5. 环境配置
    env_ok, config = check_env_config()
    results["env"] = env_ok

    # 6. 数据库连接 (仅在其他检查通过时)
    if all(results.values()):
        results["connection"] = check_database_connection(config)
    else:
        print("\n跳过数据库连接测试 (前面的检查有失败)")
        results["connection"] = False

    # 总结
    print_header("测试结果总结")

    for test, passed in results.items():
        status = "[OK] 通过" if passed else "[FAIL] 失败"
        print(f"{test:15} : {status}")

    print("\n" + "=" * 60)

    if all(results.values()):
        print_success("所有检查通过! 服务器已准备就绪。")
        print("\n下一步:")
        print("  1. 运行服务器: python simple_server.py")
        print("  2. 运行客户端: python simple_client.py")
        print("  3. 或运行测试: python simple_client.py --test")
        return 0
    else:
        print_error("部分检查失败，请解决上述问题后再试。")
        print("\n帮助:")
        print("  - 查看 INSTALL_GUIDE.md 获取详细安装指南")
        print("  - 检查 .env 文件配置")
        print("  - 确保达梦数据库客户端已正确安装")
        return 1


if __name__ == "__main__":
    sys.exit(main())
