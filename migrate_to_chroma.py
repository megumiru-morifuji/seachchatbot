import sqlite3
import chromadb
import requests
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_embedding(text: str):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"

    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text}]}
    }

    res = requests.post(url, json=payload)
    res.raise_for_status()

    return res.json()["embedding"]["values"]


def migrate():

    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("""
        SELECT id, type, question, content, answer, page, image_path
        FROM knowledge
    """)

    rows = cur.fetchall()
    conn.close()

    chroma = chromadb.PersistentClient(path="./chroma_db")

    collection = chroma.get_or_create_collection(
        name="knowledge",
        metadata={"hnsw:space": "cosine"}
    )

    for row in rows:
        id_, type_, question, content, answer, page, image = row

        # ★ embedding対象（ここ重要）
        text = f"{question or ''} {content or ''} {answer or ''}".strip()

        if not text:
            continue

        print("Embedding:", text[:50])

        embedding = get_embedding(text)

        collection.add(
            ids=[str(id_)],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                "type": type_ or "",
                "question": question or "",
                "content": content or "",
                "answer": answer or "",
                "page": str(page) if page else "",
                "image": image or ""
            }]
        )

    print("✅ 移行完了")


if __name__ == "__main__":
    migrate()
