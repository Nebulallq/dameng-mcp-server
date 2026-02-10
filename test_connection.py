"""
测试达梦数据库连接 - 尝试多种配置
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 查找并添加达梦客户端 DLL 路径
dm_home = os.getenv("DM_HOME", r"E:\Program Files\PremiumSoft\dameng_odbc_win")
if os.path.exists(os.path.join(dm_home, "dmdpi.dll")):
    os.add_dll_directory(dm_home)
    print(f"[OK] 已添加达梦客户端路径: {dm_home}")

from dmPython import connect

host = os.getenv("DAMENG_HOST", "localhost")
user = os.getenv("DAMENG_USER", "SYSDBA")
password = os.getenv("DAMENG_PASSWORD", "")

# 尝试不同的端口配置
port_configs = [
    ("默认端口 5236", 5236),
    ("JDBC 配置端口 8080", 8080),
]

print("=" * 60)
print("测试达梦数据库连接")
print("=" * 60)
print(f"主机: {host}")
print(f"用户: {user}")
print("=" * 60)

success = False
for desc, port in port_configs:
    print(f"\n尝试 {desc}...")
    config = {
        "user": user,
        "password": password,
        "server": host,
        "port": port,
    }

    try:
        print(f"  连接: {user}@{host}:{port}")
        conn = connect(**config)
        cursor = conn.cursor()

        # 测试查询
        cursor.execute("SELECT USER FROM DUAL")
        result = cursor.fetchone()
        print(f"  [成功] 当前用户: {result[0]}")

        cursor.execute("SELECT COUNT(*) FROM ALL_TABLES")
        count = cursor.fetchone()[0]
        print(f"  [成功] 可访问表数量: {count}")

        cursor.close()
        conn.close()

        success = True
        print(f"\n  连接成功! 使用端口: {port}")

        # 更新 .env 文件
        with open(".env", "r", encoding="utf-8") as f:
            content = f.read()
        content = content.replace(f"DAMENG_PORT={os.getenv('DAMENG_PORT', '5236')}", f"DAMENG_PORT={port}")
        with open(".env", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  已更新 .env 文件中的端口为 {port}")

        break

    except Exception as e:
        print(f"  [失败] {e}")

print("\n" + "=" * 60)
if success:
    print("连接测试成功!")
else:
    print("所有连接尝试均失败")
    print("\n可能的原因:")
    print("  1. 数据库服务未启动")
    print("  2. 防火墙阻止连接")
    print("  3. 用户名或密码错误")
    print("  4. 需要使用 VPN 或内网访问")
print("=" * 60)
