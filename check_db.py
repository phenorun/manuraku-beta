import sqlite3

conn = sqlite3.connect("ideas.db")
c = conn.cursor()

# すべてのデータを確認（created_at付き）
for row in c.execute("SELECT rowid, name, category, idea, note, created_at FROM ideas"):
    print(row)

conn.close()