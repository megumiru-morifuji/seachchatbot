from flask import Flask, request, jsonify,render_template
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
    return data["candidates"][0]["content"]["parts"][0]["text"]


# ===== メインAPI =====
@app.route("/ask", methods=["POST"])
def ask():

    try:
        question = request.form.get("question")
        file = request.files.get("image")

        if not question:
            return jsonify({"error": "質問が必要"}), 400

        image_bytes = file.read() if file else None

        # ===== ① DB検索 =====
        knowledge = search_knowledge(question)

        # ===== ② プロンプト作成 =====
        prompt = f"""
あなたは経費処理の専門家です。

以下のマニュアルを参考にして回答してください：

{knowledge}

質問：
{question}

ルール：
・マニュアルに基づいて答える
・不明な場合は推測しない
・簡潔に答える
"""

        # ===== ③ Gemini実行 =====
        answer = ask_gemini(prompt, image_bytes)

        return jsonify({
            "answer": answer
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/')
def home():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
