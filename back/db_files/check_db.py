import sqlite3

conn = sqlite3.connect('smart_closet.db')
cursor = conn.cursor()

# 테이블 목록 확인
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("생성된 테이블:")
for table in tables:
    print(f"  - {table[0]}")

conn.close()