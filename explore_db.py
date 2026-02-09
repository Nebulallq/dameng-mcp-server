"""
探索达梦数据库 - 列出表和结构
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 添加达梦客户端 DLL 路径
dm_home = r"E:\Program Files\PremiumSoft\dameng_odbc_win"
os.add_dll_directory(dm_home)

from dmPython import connect

config = {
    "user": os.getenv("DAMENG_USER"),
    "password": os.getenv("DAMENG_PASSWORD"),
    "server": os.getenv("DAMENG_HOST"),
    "port": int(os.getenv("DAMENG_PORT")),
}

print("=" * 60)
print("达梦数据库探索")
print("=" * 60)

with connect(**config) as conn:
    cursor = conn.cursor()

    # 1. 获取数据库版本
    print("\n[1] 数据库版本:")
    cursor.execute("SELECT * FROM V$VERSION")
    for v in cursor.fetchall():
        print(f"  {v[0]}")

    # 2. 当前用户和 Schema
    print("\n[2] 当前用户信息:")
    cursor.execute("SELECT USER, USER_ID FROM USER_USERS")
    user_info = cursor.fetchone()
    print(f"  用户: {user_info[0]}, ID: {user_info[1]}")

    # 3. 表统计
    cursor.execute("SELECT COUNT(*) FROM USER_TABLES")
    user_tables = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM ALL_TABLES")
    all_tables = cursor.fetchone()[0]
    print(f"\n[3] 表统计:")
    print(f"  用户表: {user_tables}")
    print(f"  可访问表: {all_tables}")

    # 4. 列出用户表（前30个）
    print(f"\n[4] 用户表列表 (前30个):")
    cursor.execute("SELECT TABLE_NAME FROM USER_TABLES ORDER BY TABLE_NAME")
    tables = cursor.fetchall()
    for i, t in enumerate(tables[:30], 1):
        print(f"  {i:2}. {t[0]}")

    # 5. 查看一个示例表的结构
    if tables:
        first_table = tables[0][0]
        print(f"\n[5] 表 '{first_table}' 的结构:")
        cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE FROM USER_TAB_COLUMNS WHERE TABLE_NAME = '{first_table}' ORDER BY COLUMN_ID")
        cols = cursor.fetchall()
        print(f"  {'列名':<30} {'类型':<15} {'长度':<10} {'可空'}")
        print(f"  {'-'*70}")
        for col in cols:
            print(f"  {col[0]:<30} {col[1]:<15} {col[2]:<10} {col[3]}")

    # 6. CXNP Schema 中的表
    print(f"\n[6] 搜索 CXNP 相关表:")
    cursor.execute("SELECT TABLE_NAME FROM ALL_TABLES WHERE TABLE_NAME LIKE 'CXNP%' OR OWNER LIKE 'CXNP%' ORDER BY TABLE_NAME")
    cxnp_tables = cursor.fetchall()
    if cxnp_tables:
        for i, t in enumerate(cxnp_tables[:20], 1):
            print(f"  {i:2}. {t[0]}")
        if len(cxnp_tables) > 20:
            print(f"  ... 共 {len(cxnp_tables)} 个表")
    else:
        print("  未找到 CXNP 相关表")

print("\n" + "=" * 60)
