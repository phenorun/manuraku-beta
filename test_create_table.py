import sqlite3

conn = sqlite3.connect("ideas.db")
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS ideas (
    name TEXT,
    category TEXT,
    idea TEXT,
    note TEXT
)
''')

conn.commit()
conn.close()

print("✅ テーブル 'ideas' を作成しました！")