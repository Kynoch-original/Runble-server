import os
from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS

DB_PATH = "scores.db"

def create_app():
    app = Flask(__name__)
    CORS(app)  # 🔓 Дозволити запити ззовні

    def init_db():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS best_score (nick TEXT, score INTEGER)")
        conn.commit()
        conn.close()

    @app.route("/score", methods=["POST"])
    def post_score():
        data = request.get_json()
        nick = data.get("nick")
        score = data.get("score")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Перевіряємо, чи вже є такий nick
        cursor.execute("SELECT score FROM best_score WHERE nick = ?", (nick,))
        row = cursor.fetchone()

        if row:
            # Якщо новий результат кращий — оновлюємо
            if score > row[0]:
                cursor.execute("UPDATE best_score SET score = ? WHERE nick = ?", (score, nick))
        else:
            # Якщо такого ніка немає — вставляємо
            cursor.execute("INSERT INTO best_score (nick, score) VALUES (?, ?)", (nick, score))

        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})


    @app.route("/scores", methods=["GET"])
    def get_top_scores():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT nick, score FROM best_score ORDER BY score DESC LIMIT 5")    
        results = cursor.fetchall()
        conn.close()

        top_scores = [{"nickname": nick, "score": score} for nick, score in results]
        return jsonify(top_scores), 200

    with app.app_context():
        init_db()

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
