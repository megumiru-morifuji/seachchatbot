import sqlite3
conn = sqlite3.connect("db.sqlite")
conn.execute("DELETE FROM knowledge")
conn.commit()
conn.close()
print("リセット完了")
