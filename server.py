from flask import Flask, request, jsonify
import sqlite3
import os

DB_PATH = "score.db"

def create_app():
    app = Flask(__name__)

    def init_db():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS best_score (
                nick TEXT PRIMARY KEY,
                score INTEGER NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ База ініціалізована")

    @app.route("/score", methods=["GET"])
    def get_score():
        nick = request.args.get("nick")
        if not nick:
            return jsonify({"error": "Missing nick"}), 400

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT score FROM best_score WHERE nick = ?", (nick,))
        result = cursor.fetchone()
        conn.close()

        return jsonify({"score": result[0] if result else 0})

    @app.route("/score", methods=["POST"])
    def post_score():
        data = request.get_json(force=True)
        nick = data.get("nick")
        score = data.get("score")

        if not nick or score is None:
            return jsonify({"error": "Missing nick or score"}), 400

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT score FROM best_score WHERE nick = ?", (nick,))
        result = cursor.fetchone()

        if result is None:
            cursor.execute("INSERT INTO best_score (nick, score) VALUES (?, ?)", (nick, score))
        elif score > result[0]:
            cursor.execute("UPDATE best_score SET score = ? WHERE nick = ?", (score, nick))

        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})

    @app.route("/scores", methods=["GET"])
    def get_top_scores():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT nick, score FROM best_score ORDER BY score DESC LIMIT 10")
        results = cursor.fetchall()
        conn.close()

        top_scores = [{"nickname": nick, "score": score} for nick, score in results]
        return jsonify(top_scores), 200

    with app.app_context():
        init_db()

    return app

# Глобальна змінна app, яку шукає gunicorn
app = create_app()
