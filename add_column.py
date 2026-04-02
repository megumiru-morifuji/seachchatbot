import sqlite3

conn = sqlite3.connect("db.sqlite")
cur = conn.cursor()

cur.execute("ALTER TABLE knowledge ADD COLUMN section TEXT;")

conn.commit()
conn.close()

print("pageカラム追加完了")
