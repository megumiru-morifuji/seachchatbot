import sqlite3

def search_knowledge(query):

    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("""
        SELECT type, question, answer, page, image
        FROM knowledge
        WHERE answer LIKE ?
           OR question LIKE ?
        LIMIT 5
    """, ('%' + query + '%', '%' + query + '%'))

    rows = cur.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "type": row[0],
            "question": row[1],
            "answer": row[2],
            "page": row[3],
            "image": row[4],
            "score": "LIKE検索"
        })

    return results
