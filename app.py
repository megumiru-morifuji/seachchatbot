from flask import Flask, request, render_template
import os
import requests
import base64
from dotenv import load_dotenv
from search import search_knowledge

load_dotenv()

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ===== Gemini呼び出し =====
def ask_gemini(prompt, image_bytes=None):

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    parts = [{"text": prompt}]

    # 画像がある場合
    if image_bytes:
        encoded = base64.b64encode(image_bytes).decode()
        parts.append({
            "inline_data": {
                "mime_type": "image/png",
                "data": encoded
            }
        })

    payload = {
        "contents": [
            {
                "parts": parts
            }
        ]
    }

    response = requests.post(url, json=payload)

    if response.status_code != 200:
        return f"Geminiエラー: {response.text}"

    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "回答生成に失敗しました"


# ===== プロンプト作成（RAGの核）=====
def build_prompt(results, question):

    context_text = ""

    for r in results:

        # 事例
        if r["type"] == "case":
            context_text += f"""
【事例】
質問: {r.get('question', '')}
回答: {r.get('answer', '')}
"""

        # マニュアル
        elif r["type"] == "manual":
            context_text += f"""
【マニュアル】
内容: {r.get('content', '')}
回答: {r.get('answer', '')}
ページ: {r.get('page', '')}
"""

    prompt = f"""
あなたは経費処理の専門家です。

以下の事例・マニュアルのみを根拠に回答してください：

{context_text}

質問：
{question}

ルール：
・必ず上記の情報を根拠にする
・該当情報がなければ「該当情報なし」と答える
・推測しない
・簡潔に答える
"""

    return prompt


# ===== メイン処理 =====
@app.route("/ask", methods=["POST"])
def ask():

    try:
        question = request.form.get("question")
        file = request.files.get("image")

        if not question:
            return render_template("index.html", answer="質問を入力してください", results=[])

        image_bytes = file.read() if file else None

        # ===== ① ハイブリッド検索 =====
        results = search_knowledge(question)

        # ===== ② プロンプト生成 =====
        prompt = build_prompt(results, question)

        # ===== ③ AI回答 =====
        answer = ask_gemini(prompt, image_bytes)

        # ===== ④ 画面表示 =====
        return render_template(
            "index.html",
            answer=answer,
            results=results
        )

    except Exception as e:
        return render_template("index.html", answer=f"エラー: {str(e)}", results=[])


# ===== トップページ =====
@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
