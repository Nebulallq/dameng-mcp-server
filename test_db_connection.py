"""
简单的达梦数据库连接测试脚本

用法: python test_db_connection.py
"""

import os
import sys


def test_import():
    """测试导入 dmPython"""
    print("1. 测试 dmPython 导入...")
    try:
        import dmPython
        print("   ✅ dmPython 导入成功")
        return True
    except ImportError as e:
        print(f"   ❌ dmPython 未安装: {e}")
        print("   安装命令: pip install dmPython")
        return False


def test_connection():
    """测试数据库连接"""
    print("\n2. 测试数据库连接...")

    from dotenv import load_dotenv
    load_dotenv()

    user = os.getenv("DAMENG_USER", "SYSDBA")
    password = os.getenv("DAMENG_PASSWORD", "")
    host = os.getenv("DAMENG_HOST", "localhost")
    port = os.getenv("DAMENG_PORT", "5236")

    print(f"   配置: {user}@{host}:{port}")

    if not password:
        print("   ❌ 密码未设置，请在 .env 文件中设置 DAMENG_PASSWORD")
        return False

    try:
        from dmPython import connect

        conn = connect(
            user=user,
            password=password,
            server=host,
            port=int(port)
        )
        print("   ✅ 数据库连接成功!")

        # 测试查询
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ALL_TABLES")
        count = cursor.fetchone()[0]
        print(f"   ✅ 查询成功! 发现 {count} 个表")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        return False


def test_query():
    """测试基本查询"""
    print("\n3. 测试基本查询...")

    from dotenv import load_dotenv
    load_dotenv()

    try:
        from dmPython import connect

        conn = connect(
            user=os.getenv("DAMENG_USER", "SYSDBA"),
            password=os.getenv("DAMENG_PASSWORD"),
            server=os.getenv("DAMENG_HOST", "localhost"),
            port=int(os.getenv("DAMENG_PORT", "5236"))
        )

        cursor = conn.cursor()

        # 测试查询1: 获取版本
        cursor.execute("SELECT * FROM V$VERSION")
        version = cursor.fetchone()
        print(f"   ✅ 达梦版本: {version[0] if version else 'Unknown'}")

        # 测试查询2: 列出前5个表
        cursor.execute("SELECT TABLE_NAME FROM ALL_TABLES LIMIT 5")
        tables = cursor.fetchall()
        print(f"   ✅ 表列表示例:")
        for table in tables:
            print(f"      - {table[0]}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("达梦数据库连接测试")
    print("=" * 50)

    results = []
    results.append(test_import())

    if results[0]:  # 只有 dmPython 可用时才继续测试
        results.append(test_connection())
        results.append(test_query())

    print("\n" + "=" * 50)
    if all(results):
        print("🎉 所有测试通过!")
        print("\n可以启动 MCP 服务器:")
        print("  python -m dameng_mcp_server")
    else:
        print("⚠️  请解决上述问题后重试")
    print("=" * 50)


if __name__ == "__main__":
    main()
