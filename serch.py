import sqlite3

def search_knowledge(query):

    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("""
        SELECT content, answer
        FROM knowledge
        WHERE content LIKE ?
        LIMIT 5
    """, ('%' + query + '%',))

    rows = cur.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "score": "N/A",
            "answer": row[1],
            "image": None
        })

    return results
