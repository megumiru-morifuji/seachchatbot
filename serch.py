import sqlite3
import chromadb
import requests
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ===== Chroma初期化 =====
_chroma = chromadb.PersistentClient(path="./chroma_db")
_collection = _chroma.get_or_create_collection(
    name="knowledge",
    metadata={"hnsw:space": "cosine"}
)

# ===== embedding取得 =====
def get_embedding(text: str):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"

    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text}]}
    }

    res = requests.post(url, json=payload)
    res.raise_for_status()

    return res.json()["embedding"]["values"]


# ===== メイン検索 =====
def search_knowledge(query: str, top_k: int = 5):

    results = []

    # =========================
    # ① LIKE検索（正確）
    # =========================
    conn = sqlite3.connect("db.sqlite")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM knowledge
        WHERE
            question LIKE ?
            OR content LIKE ?
            OR answer LIKE ?
            OR keywords LIKE ?
        LIMIT 10
    """, (
        f'%{query}%',
        f'%{query}%',
        f'%{query}%',
        f'%{query}%'
    ))

    like_rows = cur.fetchall()
    conn.close()

    for row in like_rows:
        results.append({
            "type": row["type"],
            "question": row["question"],
            "content": row["content"],
            "answer": row["answer"],
            "image": row["image_path"],
            "page": row["page"],
            "score": "LIKE"
        })

    # =========================
    # ② embedding検索（意味）
    # =========================
    try:
        query_embedding = get_embedding(query)

        chroma_results = _collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "distances"]
        )

        for meta, dist in zip(
            chroma_results["metadatas"][0],
            chroma_results["distances"][0]
        ):
            similarity = 1 - dist  # cosine距離→類似度

            # 閾値（重要：調整ポイント）
            if similarity < 0.6:
                continue

            results.append({
                "type": meta.get("type"),
                "question": meta.get("question"),
                "content": None,
                "answer": meta.get("answer"),
                "image": meta.get("image"),
                "page": meta.get("page"),
                "score": f"意味:{similarity:.2f}"
            })

    except Exception as e:
        print("embedding検索エラー:", e)

    # =========================
    # ③ 重複削除
    # =========================
    unique = []
    seen = set()

    for r in results:
        key = (r["answer"], r["image"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    # =========================
    # ④ 並び替え（超重要）
    # =========================
    unique.sort(key=lambda x: (
        0 if x["type"] == "case" else 1,   # 事例優先
        0 if x["score"] == "LIKE" else 1   # LIKE優先
    ))

    return unique[:10]
